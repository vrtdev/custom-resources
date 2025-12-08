import functools
import json
import os
import re
import time
import typing

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME

REGION = os.environ['AWS_REGION']
POLL_INTERVAL_SECONDS = 5
NOT_ALLOWED_IN_TOKEN = re.compile(r'\W+')


class DomainValidationNotThere(Exception):
    pass


def get_validation_records(describe_stack_response):
    result = {}
    certificate_description = describe_stack_response['Certificate']
    # If there are no DomainValidationOptions available yet, "DomainValidationOptions" may be
    # missing or not have a ResourceRecord. In both cases we raise an DomainValidationNotThere
    if "DomainValidationOptions" not in certificate_description:
        raise DomainValidationNotThere()
    for domain_validation_options in certificate_description["DomainValidationOptions"]:
        try:
            result[domain_validation_options['ResourceRecord']['Name']] = \
                domain_validation_options['ResourceRecord']['Value']
        except KeyError:
            raise DomainValidationNotThere()
    return json.dumps(result)


def add_or_replace_tag(tags: list, key: str, value: str) -> None:
    for tag in tags:
        if tag['Key'] == key:
            tag['Value'] = value
            return
    tags.append({'Key': key, 'Value': value})


class DnsValidatedCertificate(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use version ARN instead

    def validate(self):
        self.region = self.resource_properties.get('Region', REGION)
        self.domain_name = self.resource_properties['DomainName']
        self.subject_alternative_names = self.resource_properties.get(
            'SubjectAlternativeNames', None)
        self.tags = self.resource_properties.get('Tags', [])

        add_or_replace_tag(self.tags, "cr:cloudformation:stack-id", self.stack_id)

        # strip trailing dots
        if self.domain_name.endswith('.'):
            self.domain_name = self.domain_name[:-1]
        if self.subject_alternative_names is not None:
            for i, san in enumerate(self.subject_alternative_names):
                if san.endswith('.'):
                    self.subject_alternative_names[i] = san[:-1]

    @functools.lru_cache()
    def regional_acm_client(self):
        return self.get_boto3_session().client('acm', region_name=self.region)

    def update_tags(self,
                    new_tags: typing.List[typing.Dict[str, str]],
                    old_tags: typing.List[typing.Dict[str, str]] = None
                    ) -> None:
        if old_tags is None:
            old_tags = []

        if len(old_tags) > 0:
            new_tags_keys = {
                tag['Key']: True
                for tag in new_tags
            }

            to_delete = []

            for tag in old_tags:
                if tag['Key'] not in new_tags_keys:
                    to_delete.append({
                        'Key': tag['Key']
                        # omit 'value' to remove the tag regardless of value
                    })

            if len(to_delete) > 0:
                self.regional_acm_client().remove_tags_from_certificate(
                    CertificateArn=self.physical_resource_id,
                    Tags=to_delete,
                )

        if len(new_tags) > 0:
            self.regional_acm_client().add_tags_to_certificate(
                CertificateArn=self.physical_resource_id,
                Tags=new_tags,
            )

    def create(self):
        idempotency_token = NOT_ALLOWED_IN_TOKEN.sub('', self.context.aws_request_id)[:32]

        kwargs = {
            'DomainName': self.domain_name,
            'ValidationMethod': 'DNS',
            'IdempotencyToken': idempotency_token,
        }

        if self.subject_alternative_names is not None and \
                len(self.subject_alternative_names) > 0:
            kwargs['SubjectAlternativeNames'] = self.subject_alternative_names

        response = self.regional_acm_client().request_certificate(**kwargs)

        self.physical_resource_id = response['CertificateArn']

        self.update_tags(self.tags)

        return self.get_attributes()

    def get_attributes(self):
        attributes = {}
        while 'DnsRecords' not in attributes:
            try:
                description = self.regional_acm_client().describe_certificate(CertificateArn=self.physical_resource_id)
                print("Waiting for DNS records...")
                attributes['DnsRecords'] = get_validation_records(description)
            except DomainValidationNotThere:
                if self.context.get_remaining_time_in_millis() < POLL_INTERVAL_SECONDS * 1000 * 2:
                    print("DNS validation records still not available and time is up. Abort...")
                    raise RuntimeError("Timeout waiting for DNS validation records")
                print("Waiting for DNS validation records to become available...")
                time.sleep(POLL_INTERVAL_SECONDS)
        return attributes

    def update(self):
        if self.has_property_changed('Region') or \
                self.has_property_changed('DomainName'):
            return self.create()
            # CloudFormation will call delete() on the old resource
        if self.has_property_changed('SubjectAlternativeNames'):
            # If we can consider both empty, the SANs did not change. However,
            # they're represented differently in CloudFormation,
            # We consider everything that's falsy as empty ([] and None both are)
            old_san_truthy = bool(self.old_resource_properties.get('SubjectAlternativeNames'))
            new_san_truthy = bool(self.resource_properties.get('SubjectAlternativeNames'))
            if old_san_truthy or new_san_truthy:
                # at least one is not falsy / not empty
                return self.create()
                # CloudFormation will call delete() on the old resource

        self.update_tags(
            new_tags=self.tags,
            old_tags=self.old_resource_properties.get('Tags', [])
        )

        return self.get_attributes()

    def delete(self):
        try:
            self.regional_acm_client().delete_certificate(
                CertificateArn=self.physical_resource_id,
            )  # delete_certificate does not return anything
        except self.regional_acm_client().exceptions.ResourceNotFoundException:
            # Certificate was already deleted
            pass


handler = DnsValidatedCertificate.get_handler()
