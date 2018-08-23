"""
Custom Resource for managing User Pool Clients.

Parameters:
 * See http://boto3.readthedocs.io/en/latest/reference/services/cognito-idp.html#CognitoIdentityProvider.Client.create_user_pool_client

"""

import os

from cfn_custom_resource import CloudFormationCustomResource

REGION = os.environ['AWS_REGION']


def convertToBool(input):
    if isinstance(input, str):
        return input.lower() == 'true'
    else:
        return input


class UserPoolClient(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = None
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use Client Pool Id instead

    def validate(self):
        try:
            """Required"""
            self.client_name = self.resource_properties['ClientName']
            self.user_pool_id = self.resource_properties['UserPoolId']
            """Optional"""
            self.generate_secret = convertToBool(self.resource_properties.get('GenerateSecret', None))
            self.refresh_token_validity = self.resource_properties.get('RefreshTokenValidity', None)
            self.supported_identity_providers = self.resource_properties.get('SupportedIdentityProviders', None)
            self.logout_urls = self.resource_properties.get('LogoutURLs', None)
            self.callback_urls = self.resource_properties.get('CallbackURLs', None)
            self.default_redirect_uri = self.resource_properties.get('DefaultRedirectURI', None)
            self.read_attributes = self.resource_properties.get('ReadAttributes', None)
            self.write_attributes = self.resource_properties.get('WriteAttributes', None)
            self.allowed_oauth_flows = self.resource_properties.get('AllowedOAuthFlows', None)
            self.allowed_oauth_scopes = self.resource_properties.get('AllowedOAuthScopes', None)
            self.allowed_oauth_flows_user_pool_client = convertToBool(
                self.resource_properties.get('AllowedOAuthFlowsUserPoolClient', None))
            self.explicit_auth_flows = self.resource_properties.get('ExplicitAuthFlows', None)

            return True

        except (AttributeError, KeyError):
            return False

    def create(self):
        params = {'UserPoolId': self.user_pool_id, 'ClientName': self.client_name,
                       'GenerateSecret': self.generate_secret,
                       'RefreshTokenValidity': self.refresh_token_validity, 'ReadAttributes': self.read_attributes,
                       'WriteAttributes': self.write_attributes, 'ExplicitAuthFlows': self.explicit_auth_flows,
                       'SupportedIdentityProviders': self.supported_identity_providers,
                       'CallbackURLs': self.callback_urls,
                       'LogoutURLs': self.logout_urls, 'DefaultRedirectURI': self.default_redirect_uri,
                       'AllowedOAuthFlows': self.allowed_oauth_flows, 'AllowedOAuthScopes': self.allowed_oauth_scopes,
                       'AllowedOAuthFlowsUserPoolClient': self.allowed_oauth_flows_user_pool_client}
        # Remove all params that are None
        params = {k: v for k, v in params.items() if v is not None}

        boto_client = self.get_boto3_client('cognito-idp')

        response = boto_client.create_user_pool_client(**params)

        self.physical_resource_id = response["UserPoolClient"]["ClientId"]

        return {
            'ClientSecret': response["UserPoolClient"].get('ClientSecret', ''),
        }

    def update(self):
        if self.has_property_changed('GenerateSecret'):
            # We need a new GlobalTable, switch to create and let CLEANUP delete the old one
            raise ValueError("Change of GenerateSecret is not supported for update, please delete and recreate your client")

        params = {'UserPoolId': self.user_pool_id, 'ClientName': self.client_name,
                       'RefreshTokenValidity': self.refresh_token_validity, 'ReadAttributes': self.read_attributes,
                       'WriteAttributes': self.write_attributes, 'ExplicitAuthFlows': self.explicit_auth_flows,
                       'SupportedIdentityProviders': self.supported_identity_providers,
                       'CallbackURLs': self.callback_urls,
                       'LogoutURLs': self.logout_urls, 'DefaultRedirectURI': self.default_redirect_uri,
                       'AllowedOAuthFlows': self.allowed_oauth_flows, 'AllowedOAuthScopes': self.allowed_oauth_scopes,
                       'AllowedOAuthFlowsUserPoolClient': self.allowed_oauth_flows_user_pool_client}
        # Remove all params that are None
        params = {k: v for k, v in params.items() if v is not None}

        boto_client = self.get_boto3_client('cognito-idp')

        response = boto_client.update_user_pool_client(ClientId=self.physical_resource_id,
                                                       **params
                                                       )
        return {
            'ClientSecret': response["UserPoolClient"].get('ClientSecret', ''),
        }

    def delete(self):
        boto_client = self.get_boto3_client('cognito-idp')
        try:
            boto_client.delete_user_pool_client(UserPoolId=self.user_pool_id,
                                                ClientId=self.physical_resource_id)
        except boto_client.exceptions.ClientException:
            # Assume delete was successful
            pass


handler = UserPoolClient.get_handler()
