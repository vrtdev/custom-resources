from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Object(LambdaBackedCustomResource):
    props = {
        'Region': (str, False),  # Default: current region
        'Bucket': (str, True),  # Bucket name
        'Key': (str, True),  # Location within bucket
        'Body': (object, False),  # string, or JSON-able content. Default: empty file
        'ObjectMetadata': (object, False),  # dict, default: {}  ('Metadata' is reserved)
        'ContentType': (str, False),
        'CacheControl': (str, False),
    }

    @classmethod
    def _update_lambda_settings(cls, settings):
        settings['Timeout'] = 10
        return settings

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
