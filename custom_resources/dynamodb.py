from six import string_types

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class JoinGlobalTable(LambdaBackedCustomResource):
    props = {
        'TableName': (string_types, True),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "dynamodb:CreateGlobalTable",
                    "dynamodb:UpdateGlobalTable",
                ],
                "Resource": "*",
            }],
        }

    @classmethod
    def name(cls):
        """
        :rtype: List[str]
        """
        # Keep legacy non-structured name for backward compatibility
        return ['DynamoDbJoinGlobalTable']
