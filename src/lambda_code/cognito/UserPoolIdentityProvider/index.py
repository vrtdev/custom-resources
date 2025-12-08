import os

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


REGION = os.environ['AWS_REGION']


def split_resource_id(resource_id):
    parts = resource_id.split('/')
    user_pool_id = '/'.join(parts[0:-1])
    provider_name = parts[-1]

    return user_pool_id, provider_name


class UserPoolIdentityProvider(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # TODO

    def validate(self):
        try:
            self.user_pool_id = self.resource_properties['UserPoolId']
            self.provider_name = self.resource_properties['ProviderName']
            self.provider_type = self.resource_properties['ProviderType']

            self.provider_details = self.resource_properties['ProviderDetails']
            self.attribute_mapping = self.resource_properties.get('AttributeMapping', None)
            self.idp_identifiers = self.resource_properties.get('IdpIdentifiers', [])
            return True

        except (AttributeError, KeyError):
            return False

    def create(self):
        idp_client = self.get_boto3_client('cognito-idp')

        kwargs = {
            'UserPoolId': self.user_pool_id,
            'ProviderName': self.provider_name,
            'ProviderType': self.provider_type,
            'ProviderDetails': self.provider_details,
            'IdpIdentifiers': self.idp_identifiers,
        }
        if self.attribute_mapping is not None:
            # Requires a minimum of 1 mapping, so defaulting to {} is not sufficient
            kwargs['AttributeMapping'] = self.attribute_mapping

        response = idp_client.create_identity_provider(**kwargs)

        self.physical_resource_id = '/'.join([
            response["IdentityProvider"]["UserPoolId"],
            response["IdentityProvider"]["ProviderName"],
        ])
        return self.attributes()

    def update(self):
        if self.has_property_changed('UserPoolId') or \
                self.has_property_changed('ProviderName'):
            return self.create()

        if self.has_property_changed('ProviderType'):
            raise RuntimeError("ProviderType can not be changed. (Change ProviderName to create a new one)")

        idp_client = self.get_boto3_client('cognito-idp')

        kwargs = {
            'UserPoolId': self.user_pool_id,
            'ProviderName': self.provider_name,
            # No ProviderType
            'ProviderDetails': self.provider_details,
            'IdpIdentifiers': self.idp_identifiers,
        }
        if self.attribute_mapping is not None:
            kwargs['AttributeMapping'] = self.attribute_mapping

        idp_client.update_identity_provider(**kwargs)

        return self.attributes()

    def delete(self):
        user_pool_id, provider_name = split_resource_id(self.physical_resource_id)

        boto_client = self.get_boto3_client('cognito-idp')
        try:
            boto_client.delete_identity_provider(
                UserPoolId=user_pool_id,
                ProviderName=provider_name,
            )
        except (boto_client.exceptions.ResourceNotFoundException,
                boto_client.exceptions.InvalidParameterException):
            # Assume already deleted
            pass

    def attributes(self):
        return {}


handler = UserPoolIdentityProvider.get_handler()
