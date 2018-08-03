"""
Custom Resource for managing Elastic Transcoder Pipelines.
"""

import os

from cfn_custom_resource import CloudFormationCustomResource

REGION = os.environ['AWS_REGION']


def convertToBool(input):
    if isinstance(input, str):
        return input.lower() == 'true'
    else:
        return input


class ElasticTranscoderPipeline(CloudFormationCustomResource):
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use Pipeline Id instead

    def validate(self):
        try:
            """Required"""
            self.name = self.resource_properties['Name']
            if len(self.name) > 40:
                raise ValueError("Pipeline Name must be <=40 characters")
            
            self.input_bucket = self.resource_properties['InputBucket']
            self.output_bucket = self.resource_properties['OutputBucket']
            self.role = self.resource_properties['Role']
            self.notifications = self.resource_properties['Notifications']

            """Optional"""
            # none

            return True

        except (AttributeError, KeyError):
            return False

    def create(self):
        boto_client = self.get_boto3_client('elastictranscoder')

        response = boto_client.create_pipeline(
            Name=self.name,
            InputBucket=self.input_bucket,
            OutputBucket=self.output_bucket,
            Role=self.role,
            Notifications=self.notifications,
        )

        self.physical_resource_id = response[u'Pipeline'][u'Id']

        return {}

    def update(self):
        boto_client = self.get_boto3_client('elastictranscoder')

        _ = boto_client.update_pipeline(
            Id=self.physical_resource_id,
            Name=self.name,
            InputBucket=self.input_bucket,
            OutputBucket=self.output_bucket,
            Role=self.role,
            Notifications=self.notifications,
        )

        return {}

    def delete(self):
        boto_client = self.get_boto3_client('elastictranscoder')

        _ = boto_client.delete_pipeline(
            Id=self.physical_resource_id,
        )


handler = ElasticTranscoderPipeline.get_handler()
