import os

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


REGION = os.environ['AWS_REGION']


class LayerVersion(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use version ARN instead

    def validate(self):
        try:
            self.kwargs = {
                'LayerName': self.resource_properties['LayerName'],
                'Content': {
                   'S3Bucket': self.resource_properties['Content']['S3Bucket'],
                   'S3Key': self.resource_properties['Content']['S3Key'],
                },
            }
            if 'S3ObjectVersion' in self.resource_properties['Content']:
               self.kwargs['Content']['S3ObjectVersion'] = self.resource_properties['Content']['S3ObjectVersion']
            if 'CompatibleArchitectures' in self.resource_properties:
                self.kwargs['CompatibleArchitectures'] = self.resource_properties['CompatibleArchitectures']
            if 'CompatibleRuntimes' in self.resource_properties:
                self.kwargs['CompatibleRuntimes'] = self.resource_properties['CompatibleRuntimes']
            if 'Description' in self.resource_properties:
                self.kwargs['Description'] = self.resource_properties['Description']
            if 'LicenseInfo' in self.resource_properties:
                self.kwargs['LicenseInfo'] = self.resource_properties['LicenseInfo']
            return True

        except (AttributeError, KeyError):
            return False

    def create(self):
        result = self.get_boto3_client('lambda').publish_layer_version(**self.kwargs)
        self.physical_resource_id = result['LayerVersionArn']
        return {}

    def update(self):
        return self.create()

    def delete(self):
        if self.resource_properties.get('DeletionPolicy', "") == "Retain":
            return
        self.get_boto3_client('lambda').delete_layer_version(
            LayerName=self.resource_properties['LayerName'],
            Version=self.physical_resource_id.rsplit(':', 1)[-1]
        )


handler = LayerVersion.get_handler()
