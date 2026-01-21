"""
Custom Resource for waiting for an EC2 instance to be started.

This is needed for our cost-saving mode: The bringup tool will re-start the
EC2-instance, and trigger CloudFormation to re-provision the LoadBalancer.
But the instance may still be in "pending" state by the time the LoadBalancer
tries to add the instance, which will fail.
This resource simply waits for the given EC2 instance(s) to become "started",
or the Lambda times out.

Parameters:
 * InstanceIds: either a list of instance IDs, or a single InstanceId

Return:
  Ref: random
  Attributes:
   - InstanceIds: verbatim copy of input
"""
import json
import os
import time
import traceback

import six

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


REGION = os.environ['AWS_REGION']

POLL_INTERVAL = 5


class StartedWaiter(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def __init__(self, *args, **kwargs):
        super(StartedWaiter, self).__init__(*args, **kwargs)
        self.finish_function = self.finish_function_nojson
        # Can be removed once https://github.com/iRobotCorporation/cfn-custom-resource/pull/7 is accepted,
        # merged & released

    def validate(self):
        try:
            instance_ids = self.resource_properties['InstanceIds']
            if isinstance(instance_ids, list):
                self.instance_ids = set(instance_ids)
            else:
                self.instance_ids = {instance_ids}

            return True
        except (AttributeError, KeyError):
            return False

    def create(self):
        ec2_client = self.get_boto3_client('ec2')

        instance_ids_remaining = self.instance_ids.copy()
        while len(instance_ids_remaining) > 0:
            print("Waiting for: ", ", ".join(instance_ids_remaining))
            status = ec2_client.describe_instance_status(
                InstanceIds=list(instance_ids_remaining),
            )
            for instance in status['InstanceStatuses']:
                instance_id = instance['InstanceId']
                instance_state = instance['InstanceState']['Name']
                print("{} : {}".format(
                    instance_id, instance_state,
                ))
                if instance_state == 'running':
                    print("{} is running".format(instance_id))
                    instance_ids_remaining.remove(instance_id)

            if len(instance_ids_remaining) == 0:
                break  # before sleep

            if self.context.get_remaining_time_in_millis() < POLL_INTERVAL * 1000 * 2:
                raise TimeoutError("Lambda is about to timeout, still waiting for: {}".format(
                    ", ".join(instance_ids_remaining),
                ))

            time.sleep(5)
            # loop around

        return {
            'InstanceIds': self.resource_properties['InstanceIds']
        }

    def update(self):
        return self.create()

    def delete(self):
        # Nothing to delete
        pass

    @classmethod
    def finish_function_nojson(cls, resource):
        # Can be removed once https://github.com/iRobotCorporation/cfn-custom-resource/pull/7 is accepted,
        # merged & released
        physical_resource_id = resource.physical_resource_id
        if physical_resource_id is None:
            physical_resource_id = resource.context.log_stream_name
        default_reason = ("See the details in CloudWatch Log Stream: {}".format(resource.context.log_stream_name))
        outputs = {}
        for key, value in six.iteritems(resource.resource_outputs):
            outputs[key] = value
        response_content = {
            "Status": resource.status,
            "Reason": resource.failure_reason or default_reason,
            "PhysicalResourceId": physical_resource_id,
            "StackId": resource.event['StackId'],
            "RequestId": resource.event['RequestId'],
            "LogicalResourceId": resource.event['LogicalResourceId'],
            "Data": outputs
        }
        resource._base_logger.debug("Response body: {}".format(json.dumps(response_content)))
        if cls.RAISE_ON_FAILURE and resource.status == cls.STATUS_FAILED:
            raise Exception(resource.failure_reason)
        try:
            return resource.send_response_function(resource, resource.response_url, response_content)
        except Exception as e:
            resource._base_logger.error("send response failed: {}".format(e))
            resource._base_logger.debug(traceback.format_exc())


handler = StartedWaiter.get_handler()
