"""Custom resources related to Cognito."""
# wraps around http://boto3.readthedocs.io/en/latest/reference/services/cognito-idp.html#CognitoIdentityProvider.Client.create_user_pool_client

from troposphere.cognito import TokenValidityUnits

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class UserPoolClient(LambdaBackedCustomResource):
    """
    Similar to the built-in UserPoolClient, but supports the ClientSecret attribute.
    The built-in resource does not; tested 2020-06-29.
    """

    props = {
        'ClientName': (str, True),
        'UserPoolId': (str, True),
        'GenerateSecret': (bool, False),
        'SupportedIdentityProviders': ([str], False),
        'ExplicitAuthFlows': ([str], False),
        'LogoutURLs': ([str], False),
        'CallbackURLs': ([str], False),
        'DefaultRedirectURI': (str, False),
        'ReadAttributes': ([str], False),
        'WriteAttributes': ([str], False),
        'AllowedOAuthFlows': ([str], False),
        'AllowedOAuthScopes': ([str], False),
        'AllowedOAuthFlowsUserPoolClient': (bool, False),
        'RefreshTokenValidity': (int, False),
        'AccessTokenValidity': (int, False),
        'IdTokenValidity': (int, False),
        'TokenValidityUnits': (TokenValidityUnits, False),
    }



    @classmethod
    def _lambda_policy(cls):
        """
        Return the policy that the lambda function needs to function.

        This should only be the extra permissions. It will already have permissions to write logs
        :return: The policy document
        :rtype: dict

        """
        return {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Sid": "Stmt1509445937176",
                  "Action": [
                    "cognito-idp:UpdateUserPoolClient",
                    "cognito-idp:DeleteUserPoolClient",
                    "cognito-idp:CreateUserPoolClient"
                  ],
                  "Effect": "Allow",
                  "Resource": "*"
                }
              ]
            }

    @classmethod
    def name(cls):
        """
        :rtype: List[str]
        """
        # Keep legacy non-structured name for backward compatibility
        return ['CognitoUserPoolClient']


class UserPoolDomain(LambdaBackedCustomResource):
    """
    Added support for configuring the Cognito Client User Domain.
    """
    _deprecated = 1593424818
    _deprecated_message = 'cognito.UserPoolDomain is now natively supported by CloudFormation'

    props = {
        'UserPoolId': (str, True),
        'Domain': (str, False),
    }

    @classmethod
    def _lambda_policy(cls):
        """
        Return the policy that the lambda function needs to function.

        This should only be the extra permissions. It will already have permissions to write logs
        :return: The policy document
        :rtype: dict

        """
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Stmt1509445937176",
                    "Action": [
                        "cognito-idp:DeleteUserPoolDomain",
                        "cognito-idp:CreateUserPoolDomain"
                    ],
                    "Effect": "Allow",
                    "Resource": "*"
                }
            ]
        }

    @classmethod
    def name(cls):
        """
        :rtype: List[str]
        """
        # Keep legacy non-structured name for backward compatibility
        return ['CognitoUserPoolDomain']


class UserPoolIdentityProvider(LambdaBackedCustomResource):
    _deprecated = 1593424818
    _deprecated_message = 'cognito.UserPoolIdentityProvider is now natively supported by CloudFormation'

    props = {
        'UserPoolId': (str, True),
        'ProviderName': (str, True),
        'ProviderType': (str, True),
        'ProviderDetails': (dict, True),
        'AttributeMapping': (dict, False),
        'IdpIdentifiers': ([str], False),
    }

    @classmethod
    def _lambda_policy(cls):
        """
        Return the policy that the lambda function needs to function.

        This should only be the extra permissions. It will already have permissions to write logs
        :return: The policy document
        :rtype: dict

        """
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "cognito-idp:UpdateIdentityProvider",
                        "cognito-idp:DeleteIdentityProvider",
                        "cognito-idp:CreateIdentityProvider"
                    ],
                    "Effect": "Allow",
                    "Resource": "*"
                }
            ]
        }
