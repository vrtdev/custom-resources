"""Custom resources related to Cognito."""

from six import string_types

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class CognitoUserPoolDomain(LambdaBackedCustomResource):
    """
    Added support for configuring the Cognito Client User Domain.
    """

    resource_type = 'Custom::CognitoUserPoolDomain'
    props = {
        'UserPoolId': (string_types, True),
        'Domain': (string_types, False),
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
