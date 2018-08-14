import os

from cfn_custom_resource import CloudFormationCustomResource

REGION = os.environ['AWS_REGION']


class LambdaVersion(CloudFormationCustomResource):
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use version ARN instead

    def validate(self):
        try:
            self.kwargs = {
                'FunctionName': self.resource_properties['FunctionName'],
            }
            if 'CodeSha256' in self.resource_properties:
                self.kwargs['CodeSha256'] = self.resource_properties['CodeSha256']
            if 'Description' in self.resource_properties:
                self.kwargs['Description'] = self.resource_properties['Description']

            return True

        except (AttributeError, KeyError):
            return False

    def create(self):
        result = self.get_boto3_client('lambda').publish_version(**self.kwargs)
        self.physical_resource_id = result['FunctionArn']
        return {}

    def update(self):
        return self.create()

    def delete(self):
        self.get_boto3_client('lambda').delete_function(
            FunctionName=self.physical_resource_id,
        )


handler = LambdaVersion.get_handler()
