import functools
import json
import os
import re
import time

from cfn_custom_resource import CloudFormationCustomResource

REGION = os.environ['AWS_REGION']
POLL_INTERVAL_SECONDS = 5
NOT_ALLOWED_IN_TOKEN = re.compile('[\W]+')


class DomainValidationNotThere(Exception):
    pass


def get_validation_records(describe_stack_response):
    result = {}
    for domain_validation_options in describe_stack_response['Certificate']['DomainValidationOptions']:
        try:
            result[domain_validation_options['ResourceRecord']['Name']] = \
                domain_validation_options['ResourceRecord']['Value']
        except KeyError:
            raise DomainValidationNotThere()
    return json.dumps(result)


class AcmDnsValidatedCertificate(CloudFormationCustomResource):
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use version ARN instead

    def validate(self):
        self.region = self.resource_properties.get('Region', REGION)
        self.domain_name = self.resource_properties['DomainName']
        self.subject_alternative_names = self.resource_properties.get(
            'SubjectAlternativeNames', None)
        self.tags = self.resource_properties.get('Tags', [])

    @functools.lru_cache()
    def regional_acm_client(self):
        return self.get_boto3_session().client('acm', region_name=self.region)

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

        self.regional_acm_client().add_tags_to_certificate(
            CertificateArn=self.physical_resource_id,
            Tags=self.tags,
        )

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
        if self.has_property_changed('DomainName') or \
                self.has_property_changed('SubjectAlternativeNames'):
            return self.create()
            # CloudFormation will call delete() on the old resource

        if self.has_property_changed('Tags'):
            self.regional_acm_client().remove_tags_from_certificate(
                CertificateArn=self.physical_resource_id,
                Tags=self.old_resource_properties.get('Tags', []),
            )

            self.regional_acm_client().add_tags_to_certificate(
                CertificateArn=self.physical_resource_id,
                Tags=self.tags,
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


handler = AcmDnsValidatedCertificate.get_handler()
