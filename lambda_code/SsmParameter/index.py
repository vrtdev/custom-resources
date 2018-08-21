import datetime
import hashlib
import os
import random
import string
import typing

from cfn_custom_resource import CloudFormationCustomResource

REGION = os.environ['AWS_REGION']


def generate_random(specs: dict) -> str:
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


class SsmParameter(CloudFormationCustomResource):
    """
    Properties:
        Name: str: required: Name of the Parameter (including namespace)
        Description: str: optional:
        Type: enum["String", "StringList", "SecureString"]: optional:
              default "String"
        Value: str: required:
        KeyId: str: required if Type==SecureString
        RandomValue: dict: optional:
            Set Value to a random string with these properties:
             - length: int: default=22
             - charset: string: default=ascii_lowercase + ascii_uppercase + digits
             - anything-else: whatever: if it is changed, the value is regenerated
        Tags: list of {'Key': k, 'Value': v}: optional:

        ReturnValue: bool: optional: default False
            Return the value as the 'Value' attribute.
            Only useful if RandomValue is used to get the plaintext version
            (e.g. when creating RDS'es)

            Setting this option to TRUE adds additional Update restrictions:
            Any change requires a password re-generation. The resource will fail
            otherwise

        ReturnValueHash: bool: optional: default False
            Similar to ReturnValue, but returns a value that changes whenever the
            value changes in the 'ValueHash' attribute (useful to import as dummy
            environment variable to trigger a re-deploy).

            Same Update restrictions apply.
    """

    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use Name instead

    def validate(self):
        self.name = self.resource_properties['Name']

        self.description = self.resource_properties.get('Description', '')
        self.type = self.resource_properties.get('Type', 'String')

        self.value = self.resource_properties.get('Value', '')
        self.random_value = False
        if 'RandomValue' in self.resource_properties:
            self.random_value = True
            self.value = generate_random(self.resource_properties['RandomValue'])

        self.key_id = self.resource_properties.get('KeyId', None)
        self.tags = self.resource_properties.get('Tags', [])
        self.return_value = self.resource_properties.get('ReturnValue', False)
        self.return_value_hash = self.resource_properties.get('ReturnValueHash', False)

    def attributes(self):
        attr = {}

        if self.return_value:
            attr['Value'] = self.value

        if self.return_value_hash:
            if self.random_value:
                # There really is no reason for this case. The Value is given as input
                # parameter, so it's not sensitive. Requesting a hash is silly.
                # Use MD5 to "hide" the Value somewhat, but no security guarantees
                # can be given anyway
                attr['ValueHash'] = hashlib.md5(self.value.encode('utf-8')).hexdigest()
            else:
                # Password is randomly generated. Use current time as "hash".
                # We can't re-generate the same ValueHash this way, but we fail
                # Update's anyway in this case.
                attr['ValueHash'] = datetime.datetime.utcnow().isoformat()

        return attr

    def put_parameter(self, overwrite: bool = False):
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

    def update_tags(self,
                    new_tags: typing.List[typing.Dict[str, str]],
                    old_tags: typing.List[typing.Dict[str, str]] = None
                    ) -> None:
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
                    to_delete.append(tag)

            if len(to_delete) > 0:
                ssm.remove_tags_from_resource(
                    ResourceType='Parameter',
                    ResourceId=self.physical_resource_id,
                    Tags=to_delete,
                )

        ssm.add_tags_to_resource(
            ResourceType='Parameter',
            ResourceId=self.physical_resource_id,
            Tags=self.tags,
        )

    def create(self):
        return self.put_parameter(overwrite=False)

    def update(self):
        if self.has_property_changed('Name'):
            return self.create()
            # Old one will be deleted by CloudFormation

        need_put = self.has_property_changed('Description') or \
            self.has_property_changed('Type') or \
            self.has_property_changed('KeyId')

        if self.random_value and not self.has_property_changed('RandomValue'):
            # We need to maintain the previously generated Value
            # We are very limited in the updates we can perform
            if need_put:
                raise RuntimeError(
                    "Can't perform requested update: Would need to overwrite previous RandomValue, "
                    "but RandomValue should not be changed")

        self.put_parameter(overwrite=True)

        if self.has_property_changed('Tags'):
            self.update_tags(self.tags, self.old_resource_properties.get('Tags', []))

        return self.attributes()

    def delete(self):
        ssm = self.get_boto3_client('ssm')
        try:
            ssm.delete_parameter(
                Name=self.physical_resource_id,
            )
        except ssm.exceptions.ParameterNotFound:
            pass


handler = SsmParameter.get_handler()
