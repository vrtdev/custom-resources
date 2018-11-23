import time

from six import string_types

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Tags(LambdaBackedCustomResource):
    props = {
        'Dummy': (string_types, False),  # Dummy parameter to trigger updates
    }

    def __init__(self, *args, **kwargs):
        if 'Dummy' not in kwargs:
            kwargs['Dummy'] = str(time.time())  # Force refresh as much as possible

        super(Tags, self).__init__(*args, **kwargs)

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "cloudformation:DescribeStacks",
                ],
                "Resource": "*",
            }],
        }
