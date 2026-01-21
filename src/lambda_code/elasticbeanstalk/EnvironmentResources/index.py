"""
Custom Resource for Elastic Beanstalk environment resources ID's

Parameters:
    EnvironmentId:
    Serial: dummy, use this to force an update
"""

from cfn_custom_resource import CloudFormationCustomResource
try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'


class EnvironmentResources(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    eb_client = boto3.client('elasticbeanstalk')

    def validate(self):
        try:
            self.envId = self.resource_properties['EnvironmentId']
            return True

        except (AttributeError, KeyError):
            return False

    def create(self):
        attributes = {}

        result = eb_client.describe_environment_resources(EnvironmentId=self.envId)["EnvironmentResources"]
        for resourceType in result: 
            for resource in result[resourceType]:
                if isinstance(resource, dict):
                    attributes[resourceType] = resource['Name']
                    
        return attributes

    def update(self):
        return self.create()

    def delete(self):
        # Nothing to delete
        pass


handler = EnvironmentResources.get_handler()
