from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Server(LambdaBackedCustomResource):
    props = {
        'EndpointType': (str, False),  # Default: PUBLIC
        'EndpointDetails': (dict, False),  # only needed if endpoint type is VPC_ENDPOINT
        'HostKey': (str, False),
        'IdentityProviderType': (str, False),  # Default: SERVICE_MANAGED
        'IdentityProviderDetails': (dict, False),  # only needed if identity provider is API_GATEWAY
        'LoggingRole': (str, False),
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
                    "iam:PassRole"
                ],
                "Resource": "*",
            }],
        }


class User(LambdaBackedCustomResource):
    props = {
        'HomeDirectory': (str, False),  # will default to /{UserName}
        'Role': (str, True),  # will need permissions to access a bucket
        'Policy': (str, False),
        'ServerId': (str, True),
        'SshPublicKeyBody': (str, True),  # base64 encoded
        'UserName': (str, True),
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
