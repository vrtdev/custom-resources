"""
Custom Resource for managing User Pool Clients.

Parameters:
 * See http://boto3.readthedocs.io/en/latest/reference/services/cognito-idp.html#CognitoIdentityProvider.Client.create_user_pool_client

"""

import os

from cfn_custom_resource import CloudFormationCustomResource

REGION = os.environ['AWS_REGION']


class CognitoUserPoolClient(CloudFormationCustomResource):
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use Client Pool Id instead

    def validate(self):
        try:
            """Required"""
            self.client_name = self.resource_properties['ClientName']
            self.user_pool_id = self.resource_properties['UserPoolId']
            """Optional"""
            generate_secret = self.resource_properties.get('GenerateSecret', None)
            refresh_token_validity = self.resource_properties.get('RefreshTokenValidity', None)
            supported_identity_providers = self.resource_properties.get('SupportedIdentityProviders', None)
            logout_urls = self.resource_properties.get('LogoutURLs', None)
            callback_urls = self.resource_properties.get('CallbackURLs', None)
            default_redirect_uri = self.resource_properties.get('DefaultRedirectURI', None)
            read_attributes = self.resource_properties.get('ReadAttributes', None)
            write_attributes = self.resource_properties.get('WriteAttributes', None)
            allowed_oauth_flows = self.resource_properties.get('AllowedOAuthFlows', None)
            allowed_oauth_scopes = self.resource_properties.get('AllowedOAuthScopes', None)
            allowed_oauth_flows_user_pool_client = self.resource_properties.get('AllowedOAuthFlowsUserPoolClient', None)
            explicit_auth_flows = self.resource_properties.get('ExplicitAuthFlows', None)

            self.params = {'UserPoolId': self.user_pool_id, 'ClientName': self.client_name,
                           'GenerateSecret': generate_secret,
                           'RefreshTokenValidity': refresh_token_validity, 'ReadAttributes': read_attributes,
                           'WriteAttributes': write_attributes, 'ExplicitAuthFlows': explicit_auth_flows,
                           'SupportedIdentityProviders': supported_identity_providers, 'CallbackURLs': callback_urls,
                           'LogoutURLs': logout_urls, 'DefaultRedirectURI': default_redirect_uri,
                           'AllowedOAuthFlows': allowed_oauth_flows, 'AllowedOAuthScopes': allowed_oauth_scopes,
                           'AllowedOAuthFlowsUserPoolClient': allowed_oauth_flows_user_pool_client}
            # convert strings to bool where needed:
            for k in ['AllowedOAuthFlowsUserPoolClient', 'GenerateSecret']:
                # convert string to boolean
                if isinstance(self.params[k], str):
                    self.params[k] = self.params[k].lower() == 'true'
            # Remove all params that are None
            self.params = {k: v for k, v in self.params.items() if v is not None}

            return True

        except (AttributeError, KeyError):
            return False

    def create(self):
        boto_client = self.get_boto3_client('cognito-idp')

        response = boto_client.create_user_pool_client(**self.params)

        self.physical_resource_id = response["UserPoolClient"]["ClientId"]

        return {
            'ClientSecret': response["UserPoolClient"].get('ClientSecret', ''),
        }

    def update(self):
        boto_client = self.get_boto3_client('cognito-idp')

        response = boto_client.update_user_pool_client(ClientId=self.physical_resource_id,
                                                       **self.params
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


handler = CognitoUserPoolClient.get_handler()
