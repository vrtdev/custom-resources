"""ParseDict custom resource.

ParseDict custom resource lambda to read json formatted ssm ps parameters
and return them in easy to work with dict structures.
"""
from collections import ChainMap
import os
import json

from cfn_custom_resource import CloudFormationCustomResource

try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'

REGION = os.environ['AWS_REGION']


class ParseDict(CloudFormationCustomResource):
    """
    ssm.ParseDict.

    Properties:
        Names: List[str]: List of parameter paths (including namespace) to read
        Serial: str: Use this to force an update
    """

    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def validate(self):
        self.names = self.resource_properties.get('Names')
        if not self.names:
            return False
        return True

    def create(self):
        ssm = self.get_boto3_client('ssm')
        print(f"Retrieving parameters with paths '{self.names}'")
        params = ssm.get_parameters(Names=self.names)
        value = dict(ChainMap(*[json.loads(param['Value']) for param in params['Parameters']]))
        print(f"Got merged value: '{value}'")
        return value

    def update(self):
        return self.create()

    def delete(self):
        # Nothing to delete
        pass


handler = ParseDict.get_handler()
