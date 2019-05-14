from six import string_types

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Object(LambdaBackedCustomResource):
    props = {
        'Region': (string_types, False),  # Default: current region
        'Bucket': (string_types, True),  # Bucket name
        'Key': (string_types, True),  # Location within bucket
        'Body': (object, False),  # string, or JSON-able content. Default: empty file
        'Metadata': (object, False),  # dict, default: {}
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:DeleteObject",
                ],
                "Resource": "*",
            }],
        }
