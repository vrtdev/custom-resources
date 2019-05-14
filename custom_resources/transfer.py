from six import string_types

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Server(LambdaBackedCustomResource):
    props = {
        'EndpointType': (string_types, False),  # Default: PUBLIC
        'EndpointDetails': (dict, False),  # only needed if endpoint type is VPC_ENDPOINT
        'HostKey': (string_types, False),
        'IdentityProviderType': (string_types, False),  # Default: SERVICE_MANAGED
        'IdentityProviderDetails': (dict, False),  # only needed if identity provider is API_GATEWAY
        'LoggingRole': (string_types, False),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "transfer:CreateServer",
                    "transfer:DeleteServer",
                    "transfer:DescribeServer",
                    "transfer:List*",
                    "transfer:StartServer",
                    "transfer:StopServer",
                    "transfer:TestIdentityProvider",
                    "transfer:UpdateServer",
                ],
                "Resource": "*",
            }],
        }


class User(LambdaBackedCustomResource):
    props = {
        'HomeDirectory': (string_types, False),  # will default to /{UserName}
        'Role': (string_types, True),  # will need permissions to access a bucket
        'Policy': (string_types, False),
        'ServerId': (string_types, True),
        'SshPublicKeyBody': (string_types, True),  # base64 encoded
        'UserName': (string_types, True),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "transfer:CreateUser",
                    "transfer:DeleteUser",
                    "transfer:DeleteSshPublicKey",
                    "transfer:DescribeUser",
                    "transfer:ImportSshPublicKey",
                    "transfer:List*",
                    "transfer:UpdateUser",
                    "iam:PassRole"
                ],
                "Resource": "*",
            }],
        }
