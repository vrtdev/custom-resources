import os

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


REGION = os.environ['AWS_REGION']


class Tags(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def create(self):
        stack_region = self.stack_id.split(':')[3]
        boto_client_in_region = self.get_boto3_session().client(
            'cloudformation',
            region_name=stack_region
        )

        stack_description = boto_client_in_region.describe_stacks(
            StackName=self.stack_id,
        )
        stack_description = stack_description['Stacks'][0]
        tags = stack_description['Tags']

        return {
            'TagList': tags,
            'TagDict': {
                tag['Key']: tag['Value']
                for tag in tags
            },
        }

    def update(self):
        return self.create()

    def delete(self):
        pass


handler = Tags.get_handler()
