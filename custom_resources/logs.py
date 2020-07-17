"""
Custom resource to support Amazon Cloudwatch Logs ResourcePolicy as Cloudformation doesn't support this yet.
You can vote to support it at https://github.com/aws-cloudformation/aws-cloudformation-coverage-roadmap/issues/249
"""
from .LambdaBackedCustomResource import LambdaBackedCustomResource


class ResourcePolicy(LambdaBackedCustomResource):
    props = {
        'PolicyDocument': (dict, True),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "logs:PutResourcePolicy",
                    "logs:DeleteResourcePolicy",
                ],
                "Resource": "*",
            }],
        }
