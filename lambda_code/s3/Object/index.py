import json
import os

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


REGION = os.environ['AWS_REGION']


class S3Object(CloudFormationCustomResource):
    """
    Properties:
      Region: str: region of bucket (default: current region)
      Bucket: str: bucket name
      Key: str: location within bucket
      Body: str: content of object to create/update
    """
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use s3-path instead

    def validate(self):
        self.region = self.resource_properties.get('Region', REGION)
        self.bucket = self.resource_properties['Bucket']
        self.key = self.resource_properties['Key']
        self.body = self.resource_properties.get('Body', '')
        self.object_metadata = self.resource_properties.get('ObjectMetadata', {})
        self.content_type = self.resource_properties.get('ContentType', 'binary/octet-stream')  # copy AWS default
        self.cache_control = self.resource_properties.get('CacheControl', None)
        self.allow_overwrite = self.resource_properties.get('AllowOverwrite', False)

        if not isinstance(self.body, str):
            self.body = json.dumps(self.body)

    def create(self, allow_overwrite_override = False):

        optional_props = {}
        if self.cache_control is not None:
            optional_props['CacheControl'] = self.cache_control

        if self.allow_overwrite is False and allow_overwrite_override is False:
            optional_props['IfNoneMatch'] = '*'

        s3_client = self.get_boto3_session().client('s3', region_name=self.region)
        s3_client.put_object(
            Bucket=self.bucket,
            Key=self.key,
            Body=self.body.encode('utf-8'),
            Metadata=self.object_metadata,
            ContentType=self.content_type,
            **optional_props,
        )
        # set the resource id after creation so we can't delete by accident
        self.physical_resource_id = f"{self.bucket}/{self.key}"

    def update(self):
        if self.has_property_changed('Key') or self.has_property_changed('Bucket'):
            return self.create()
        else:  # Key or Bucket hasn't changed
            return self.create(allow_overwrite_override=True)

    def delete(self):
        # Split the string at the first occurrence of sep, and return a 3-tuple
        # If the separator is not found, return a 3-tuple containing the string itself, followed by two empty strings.
        bucket, sep, key = self.physical_resource_id.partition("/")
        if not key:
            # nothing to do - create failed
            return

        s3_client = self.get_boto3_session().client('s3', region_name=self.region)
        s3_client.delete_object(
            Bucket=bucket,
            Key=key,
        )


handler = S3Object.get_handler()
