"""Custom Resource to create an SSM Parameter."""

import base64
import json
import os
import random
import string
import typing

from cfn_custom_resource import CloudFormationCustomResource

from lambda_shared import strtobool

try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'

REGION = os.environ['AWS_REGION']

ENCODE = {
    'none': lambda x: x,
    'base64': lambda x: base64.b64encode(x.encode('utf-8')).decode('utf-8'),
}


def generate_random(specs: dict) -> str:
    """Generate a random string."""
    length = int(specs.get('length', 22))
    charset = specs.get('charset',
                        string.ascii_uppercase +
                        string.ascii_lowercase +
                        string.digits)
    r = ''.join([
        random.SystemRandom().choice(charset)
        for _ in range(length)
    ])
    return r


class Parameter(CloudFormationCustomResource):
    """
    Custom Resource class to create an SSM Parameter with some features that aren't currently available through standard CloudFormation.

    Properties:
        Name: str: optional: Name of the Parameter (including namespace)
        Description: str: optional:
        Type: enum["String", "StringList", "SecureString"]: optional:
              default "String"
        KeyId: str: required if Type==SecureString
        Value: str: required unless using ValueFrom or RandomValue
        ValueFrom: str: optional:
            ARN of another parameter, which can be found in SSM or SecretsManager,
            and where the Value is retrieved from.
        RandomValue: dict: optional:
            Set Value to a random string with these properties:
             - length: int: default=22
             - charset: string: default=ascii_lowercase + ascii_uppercase + digits
             - anything-else: whatever: if it is changed, the value is regenerated
        Encoding: str: optional: default "none", options: "none", "base64"
        Tags: list of {'Key': k, 'Value': v}: optional:

        ReturnValue: bool: deprecated
    """

    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use Name instead

    def validate(self):
        """Validate input parameters."""
        self.name = self.resource_properties.get('Name')
        if self.name is None:
            self.name = self.generate_unique_id(
                prefix="CFn-",
                max_len=2048,
            )

        self.description = self.resource_properties.get('Description', '')
        self.type = self.resource_properties.get('Type', 'String')

        self.value = self.resource_properties.get('Value', '')
        self.random_value = False
        if 'ValueFrom' in self.resource_properties:
            self.value = self.fetch_value(self.resource_properties['ValueFrom'])
        if 'RandomValue' in self.resource_properties:
            self.random_value = True
            self.value = generate_random(self.resource_properties['RandomValue'])
        self.encoding = self.resource_properties.get('Encoding', 'none')
        try:
            self.value = ENCODE[self.encoding](self.value)
        except KeyError:
            raise ValueError(f"Invalid encoding value: {self.encoding}. Supported encodings: {','.join(ENCODE.keys())}")

        self.key_id = self.resource_properties.get('KeyId', None)
        self.tags = self.resource_properties.get('Tags', [])

    def attributes(self):
        """Construct the attributes to return to CloudFormation."""
        account_id = self.context.invoked_function_arn.split(":")[4]
        attr = {
            'Arn': f'arn:aws:ssm:{REGION}:{account_id}:parameter{self.name}',
            'Value': ''.join([
                '{{',
                ':'.join([
                    'resolve',
                    'ssm-secure' if self.type == 'SecureString' else 'ssm',
                    self.physical_resource_id,
                ]),
                '}}',
            ]) if self.random_value else self.value,
        }

        return attr

    def fetch_value(self, value_from: str):
        """Fetch the value from another parameter."""
        svc = value_from.split(':')[2]
        match svc:
            case 'ssm':
                ssm = self.get_boto3_client(svc)
                try:
                    response = ssm.get_parameter(
                        Name=value_from,
                        WithDecryption=True,
                    )
                    return response['Parameter']['Value']
                except ssm.exceptions.ParameterNotFound:
                    raise ValueError(f"Parameter {value_from} not found")
            case 'secretsmanager':
                secretsmanager = self.get_boto3_client(svc)
                try:
                    # value_from = arn:aws:secretsmanager:region:aws_account_id:secret:secret-name:json-key:version-stage:version-id
                    # GetSecretValue does not accept ARNs that include the json-key.
                    # We need to parse the value ourselves and return the correct value if json-key is present.
                    arn_parts = value_from.split(':')
                    json_key = arn_parts[7]
                    extras = {k: v for k, v in zip(['VersionId', 'VersionStage'], arn_parts[8:]) if v}
                    response = secretsmanager.get_secret_value(
                        SecretId=':'.join(arn_parts[0:7]),
                        **extras,
                    )
                    return json.loads(response['SecretString']).get(json_key)
                except secretsmanager.exceptions.ResourceNotFoundException:
                    raise ValueError(f"Secret {value_from} not found")
            case _:
                raise ValueError(f"Unknown value_from: {value_from}")

    def put_parameter(self, overwrite: bool = False):
        """Use AWS API to create or update the parameter."""
        ssm = self.get_boto3_client('ssm')
        params = {
            'Name': self.name,
            'Type': self.type,
            'Value': self.value,
            'Description': self.description,
            'Overwrite': overwrite,
        }
        if self.key_id is not None:
            params['KeyId'] = self.key_id

        _ = ssm.put_parameter(**params)
        self.physical_resource_id = self.name

        self.update_tags(self.tags)

        return self.attributes()

    def update_tags(
            self,
            new_tags: typing.List[typing.Dict[str, str]],
            old_tags: typing.List[typing.Dict[str, str]] = None,
    ) -> None:
        """Update tags on the resource."""
        if old_tags is None:
            old_tags = []

        ssm = self.get_boto3_client('ssm')

        if len(old_tags) > 0:
            new_tags_keys = {
                tag['Key']: True
                for tag in new_tags
            }

            to_delete = []

            for tag in old_tags:
                if tag['Key'] not in new_tags_keys:
                    to_delete.append(tag['Key'])

            if len(to_delete) > 0:
                ssm.remove_tags_from_resource(
                    ResourceType='Parameter',
                    ResourceId=self.physical_resource_id,
                    TagKeys=to_delete,
                )

        ssm.add_tags_to_resource(
            ResourceType='Parameter',
            ResourceId=self.physical_resource_id,
            Tags=self.tags,
        )

    def create(self):
        """Create the resource."""
        return self.put_parameter(overwrite=False)

    def update(self):
        """Update the resource."""
        can_put = (not self.random_value) or \
                  (self.random_value and self.has_property_changed('RandomValue'))

        need_put = self.has_property_changed('Name') or \
            self.has_property_changed('Description') or \
            self.has_property_changed('Type') or \
            self.has_property_changed('KeyId') or \
            self.has_property_changed('Encoding') or \
            self.has_property_changed('Value') or \
            self.has_property_changed('ValueFrom') or \
            self.has_property_changed('RandomValue')

        if need_put and not can_put:
            # We need to maintain the previously generated Value
            # We are very limited in the updates we can perform
            raise RuntimeError(
                "Can't perform requested update: Would need to overwrite previous RandomValue, "
                "but RandomValue should not be changed")

        if self.has_property_changed('Name'):
            return self.create()
            # Old one will be deleted by CloudFormation

        if need_put:
            print("Updating parameter")
            self.put_parameter(overwrite=True)

        if self.has_property_changed('Tags'):
            print("Updating tags")
            self.update_tags(self.tags, self.old_resource_properties.get('Tags', []))

        return self.attributes()

    def delete(self):
        """Delete the resource."""
        ssm = self.get_boto3_client('ssm')
        try:
            ssm.delete_parameter(
                Name=self.physical_resource_id,
            )
        except ssm.exceptions.ParameterNotFound:
            pass


handler = Parameter.get_handler()
