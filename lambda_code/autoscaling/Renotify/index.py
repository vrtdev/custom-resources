import json

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


class RenotifyAsg(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def validate(self):
        self.asg_name = self.resource_properties['AutoScalingGroupName']

    def create(self):
        as_client = self.get_boto3_client('autoscaling')
        sns_client = self.get_boto3_client('sns')

        notification_paginator = as_client.get_paginator('describe_notification_configurations')
        notification_iterator = notification_paginator.paginate(
            AutoScalingGroupNames=[
                self.asg_name,
            ],
        )
        for page in notification_iterator:
            for notification in page['NotificationConfigurations']:
                sns_client.publish(
                    TopicArn=notification['TopicARN'],
                    Message=json.dumps({
                        "AutoScalingGroupName": self.asg_name,
                        # TODO: this is incomplete; add additional fields
                    }),
                )

        return {}

    def update(self):
        return self.create()

    def delete(self):
        pass


handler = RenotifyAsg.get_handler()
