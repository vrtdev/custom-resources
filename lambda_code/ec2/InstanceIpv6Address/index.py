"""
Custom Resource for extracting the ipv6 address of an EC2 instance.

This feature is currently not supported natively by cloudformation.
An open feature request can be found here:
https://github.com/aws-cloudformation/cloudformation-coverage-roadmap/issues/916
This custom resource will check the network interface of the given instance and output
the associated ipv6 address.

Parameters:
 * InstanceId: a single InstanceId

Return:
  Attributes:
   - Ipv6Address: The ipv6 address of the given instance
"""
import os

from cfn_custom_resource import CloudFormationCustomResource
try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'

REGION = os.environ['AWS_REGION']


class InstanceIpv6Address(CloudFormationCustomResource):
    """
    ec2.InstanceIpv6Address

    Properties:
        InstanceId: str: The instance id to retrieve the ipv6 address from
    """
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def validate(self):
        self.instance_id = self.resource_properties['InstanceId']
        return self.instance_id.startswith("i-")

    def create(self):
        ec2_client = self.get_boto3_client('ec2')
        print(f"Retrieving network interface info for '{self.instance_id}'")
        resp = ec2_client.describe_network_interfaces(
            Filters=[{'Name':'attachment.instance-id', 'Values':[self.instance_id] }]
        )
        address = resp.get('NetworkInterfaces')[0]['Ipv6Address']
        print(f"Found address '{address}' associated with instance '{self.instance_id}'")
        return {
            'Ipv6Address': address
        }

    def update(self):
        return self.create()

    def delete(self):
        # Nothing to delete
        pass


handler = InstanceIpv6Address.get_handler()
