from six import string_types
from troposphere import Tags

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class AssociateVPCEndpoint(LambdaBackedCustomResource):
    props = {
        'RestApiId': (string_types, True),
        'VpcEndpointId': (string_types, False),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "apigateway:PATCH",  # update-rest-api
                ],
                "Resource": "*",
            }],
        }
