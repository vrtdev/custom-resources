from six import string_types

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class MySQLUser(LambdaBackedCustomResource):
    props = {
        'User': (string_types, True),
        'Password': (string_types, False),
        'PasswordParameterName': (string_types, False),
        'PasswordSecretName': (string_types, False),
        'WithDatabase': (bool, False),
        'DeletionPolicy': (string_types, False),
        'Database': (dict, True),
    }

    @classmethod
    def _update_lambda_settings(cls, settings):
        # It can take a while to connect and add/update/remove users
        settings['Timeout'] = 300
        
        # Since it is a submodule, the handler is located in another location
        settings['Handler'] = 'src/mysql_user_provider.handler'

        # Enable Vpc config for this resource to be able to connect to a rds instance
        settings['VpcConfig'] = {}

        return settings

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ssm:GetParameter",
                        "secretsmanager:GetSecretValue",
                    ],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "kms:Decrypt",
                    ],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:*",
                    ],
                    "Resource": "arn:aws:logs:*:*:*",
                },
            ],
        }

    @classmethod
    def name(cls):
        """
        :rtype: List[str]
        """
        # Keep non-structured name because upstream lambda code sets it this way
        return ['MySQLUser']