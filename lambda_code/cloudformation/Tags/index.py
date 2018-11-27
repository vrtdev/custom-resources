import json
import os
import traceback

import six
from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


REGION = os.environ['AWS_REGION']


class Tags(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def __init__(self, *args, **kwargs):
        super(Tags, self).__init__(*args, **kwargs)
        self.finish_function = self.finish_function_nojson
        # Can be removed once https://github.com/iRobotCorporation/cfn-custom-resource/pull/7 is accepted,
        # merged & released

    def validate(self):
        self.omit = self.resource_properties.get('Omit', [])
        self.set = self.resource_properties.get('Set', {})

    def create(self):
        stack_region = self.stack_id.split(':')[3]

        print(f"Getting tags set on {self.stack_id} in region {stack_region}")

        boto_client_in_region = self.get_boto3_session().client(
            'cloudformation',
            region_name=stack_region
        )

        stack_description = boto_client_in_region.describe_stacks(
            StackName=self.stack_id,
        )
        stack_description = stack_description['Stacks'][0]
        tags_dict = {
            tag['Key']: tag['Value']
            for tag in stack_description['Tags']
        }
        print("Found tags:")
        print(json.dumps(tags_dict))

        for key in self.omit:
            tags_dict.pop(key, None)

        for key, value in self.set.items():
            tags_dict[key] = value

        print("Tags after Omit/Set:")
        print(json.dumps(tags_dict))

        return {
            'TagDict': tags_dict,
            'TagList': [
                {'Key': k, 'Value': v}
                for k, v in tags_dict.items()
            ],
        }

    def update(self):
        return self.create()

    def delete(self):
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


handler = Tags.get_handler()
