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
    def _update_lambda_settings(cls, settings):
        settings['Timeout'] = 60  # Default timeout of 3 seconds is not always long enough.
        return settings

    @classmethod
    def name(cls):
        """
        :rtype: List[str]
        """
        # Keep legacy non-structured name for backward compatibility
        return ['DynamoDbJoinGlobalTable']


class Item(LambdaBackedCustomResource):
    props = {
        'Region': (string_types, False),
        'TableName': (string_types, True),
        'ItemKey': (dict, True),
        'ItemValue': (dict, False),
        'Overwrite': (bool, False),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "dynamodb:DeleteItem",
                    "dynamodb:PutItem",
                ],
                "Resource": "*",
            }],
        }
