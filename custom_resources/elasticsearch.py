"""Custom resources related to Elasticsearch."""
from six import string_types
from .LambdaBackedCustomResource import LambdaBackedCustomResource


class IngestPipeline(LambdaBackedCustomResource):
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
