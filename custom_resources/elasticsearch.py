"""Custom resources related to Elasticsearch."""
from six import string_types
from .LambdaBackedCustomResource import LambdaBackedCustomResource


class IngestPipelineViaVpc(LambdaBackedCustomResource):
    props = {
        'EsHost': (string_types, True),
        'PipelineName': (string_types, True),
        'IngestDocument': (dict, True),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": "es:ESHttp*",
                "Resource": "*",
            }],
        }

    @classmethod
    def _update_lambda_settings(cls, settings):
        """
        Update the default settings for the lambda function.

        :param settings: The default settings that will be used
        :return: updated settings
        """
        settings['VpcConfig'] = {}  # build.py adds the config if the key is present
        return settings
