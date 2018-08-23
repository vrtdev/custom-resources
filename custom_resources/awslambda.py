from six import string_types

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Version(LambdaBackedCustomResource):
    props = {
        'FunctionName': (string_types, True),
        'Description': (string_types, False),
        'CodeSha256': (string_types, False),
        'Dummy': (string_types, False),  # Dummy parameter to trigger updates
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "lambda:ListVersionsByFunction",
                    "lambda:PublishVersion",
                    "lambda:DeleteFunction",  # Yes, you need to DeleteFunction("func:version") to delete a version
                ],
                "Resource": "*",
            }],
        }
