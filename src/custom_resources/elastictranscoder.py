"""Custom resources related to ElasticTranscoder."""
from six import string_types

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Pipeline(LambdaBackedCustomResource):
    """
    Added support for configuring the Cognito Client User Pool.
    """

    props = {
        'Name': (string_types, True),
        'InputBucket': (string_types, True),
        'OutputBucket': (string_types, True),
        'Role': (string_types, True),
        'Notifications': (dict, True),
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
                    "Effect": "Allow",
                    "Action": [
                        "elastictranscoder:CreatePipeline",
                        "elastictranscoder:DeletePipeline",
                        "elastictranscoder:ReadPipeline",
                        "elastictranscoder:UpdatePipeline"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "Stmt1441234334958",
                    "Action": [
                        "iam:PassRole"
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
        return ['ElasticTranscoderPipeline']
