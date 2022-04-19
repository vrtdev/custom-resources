"""ParseDict custom resource.

ParseDict custom resource lambda to read json formatted ssm ps parameters
and return them in easy to work with dict structures.
"""
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
        Name: str: Name of the Parameter (including namespace)
        Serial: str: Use this to force an update
    """

    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    # TODO: figure out if we need this or not
    # DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True

    def validate(self):
        self.name = self.resource_properties.get('Name')
        if not self.name:
            return False
        return True

    def create(self):
        ssm = self.get_boto3_client('ssm')
        print(f"Retrieving parameter with path '{self.name}'")
        param = ssm.get_parameter(Name=self.name)
        print(f"Got value: '{param['Parameter']['Value']}'")
        return json.loads(param['Parameter']['Value'])

    def update(self):
        return self.create()

    def delete(self):
        # Nothing to delete
        pass


handler = ParseDict.get_handler()
