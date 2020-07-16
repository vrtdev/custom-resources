"""
Custom resource to support Amazon Cloudwatch Logs ResourcePolicy.
https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_ResourcePolicy.html
https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_PutResourcePolicy.html
https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_DeleteResourcePolicy.html
"""

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


class ResourcePolicy(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def validate(self):
        self.policy_doc = self.resource_properties['PolicyDocument']

    def create(self):
        cl = self.get_boto3_client('logs')
        cl.put_resource_policy(policyName=self.physical_resource_id, policyDocument=self.policy_doc)
        return {}

    def update(self):
        return self.create()

    def delete(self):
        cl = self.get_boto3_client('logs')
        try:
            cl.delete_resource_policy(policyName=self.physical_resource_id)
        except (cl.exceptions.ResourceNotFoundException,
                cl.exceptions.InvalidParameterException):
            # Assume already deleted
            pass


handler = ResourcePolicy.get_handler()
