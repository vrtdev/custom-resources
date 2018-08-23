"""
Custom Resource for finding latest the AMI id for a given Description

Parameters:
 * Region: (default: current region)
 * Name: Like: "amzn-ami-minimal-hvm*"
 * OwnerAlias
 * OwnerId
 * Architecture: Defaults to: "x86_64",
 * DeviceType: Defaults to: "ebs",
 * VirtualizationType: Defaults to: "hvm",
 * State: Defaults to: 'available',
"""

import os
import boto3

from cfn_custom_resource import CloudFormationCustomResource

REGION = os.environ['AWS_REGION']


def dict_element_copy_if_exists(
        source_dict: dict, source_key: str,
        target_dict: dict, target_key: str):
    if source_key in source_dict:
        target_dict[target_key] = source_dict[source_key]


class FindAmi(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = None
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Return AMI ID as physical ID

    def validate(self):
        self.filter = {}

        try:
            self.filter['name'] = self.resource_properties['Name']
            dict_element_copy_if_exists(
                self.resource_properties, 'OwnerAlias',
                self.filter, 'owner-alias'
            )
            dict_element_copy_if_exists(
                self.resource_properties, 'OwnerId',
                self.filter, 'owner-id'
            )
            self.filter['architecture'] = self.resource_properties.get('Architecture', 'x86_64')
            self.filter['root-device-type'] = self.resource_properties.get('DeviceType', 'ebs')
            self.filter['virtualization-type'] = self.resource_properties.get('VirtualizationType', 'hvm')
            self.filter['state'] = self.resource_properties.get('State', 'available')
            return True

        except (AttributeError, KeyError):
            return False

    def create(self):
        ec2_client = boto3.client(  # Don't use self.get_boto3_client, since we may vary regions
            'ec2',
            region_name=self.resource_properties.get('Region', REGION),
        )

        ami_filter = []
        for key, value in self.filter.items():
            ami_filter.append({
                'Name': key,
                'Values': [value],
            })

        ami_list = ec2_client.describe_images(
            Filters=ami_filter
        )
        sorted_ami_list = sorted(
            ami_list['Images'],
            key=lambda k: k.get('CreationDate', ''),
            reverse=True
        )
        if len(sorted_ami_list) == 0:
            self.status = self.STATUS_FAILED
            self.failure_reason = "No image found matching filters."
            return {}

        latest_ami = sorted_ami_list[0]
        self.physical_resource_id = latest_ami['ImageId']
        return {}

    def update(self):
        return self.create()

    def delete(self):
        # Nothing to delete
        pass


handler = FindAmi.get_handler()
