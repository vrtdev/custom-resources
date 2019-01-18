"""
Custom Resource for adding an item into a DynamoDB table

Parameters:
 * Region: optional: region where the DynamoDB table is located. Default: current region of the Lambda
 * TableName: required: name of the tables to join.
 * ItemKey: required: Key Attributes and their values
 * ItemValue: optional: Other Attributes and their values
"""
import functools
import os

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME

NOT_CREATED = "NOT CREATED"

REGION = os.environ['AWS_REGION']


class Item(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Encode key into ID

    @functools.lru_cache()
    def regional_dynamodb_client(self):
        return self.get_boto3_session().client('dynamodb', region_name=self.region)

    def validate(self):
        self.region = self.resource_properties.get('Region', REGION)
        self.table_name = self.resource_properties['TableName']
        self.item_key = self.resource_properties['ItemKey']
        self.item_value = self.resource_properties.get('ItemValue', {})
        self.overwrite = self.resource_properties.get('Overwrite', False)

        for key in self.item_key.keys():
            if key in self.item_value:
                raise ValueError(f"Attribute {key} listed in both ItemKey and ItemValue")

    def construct_item(self):
        # Construct item, which is one dict of both key and value
        item = {}
        item.update(self.item_key)
        item.update(self.item_value)
        return item

    def construct_physical_id(self):
        key = ','.join([
            f"{k}={v}"
            for k, v in sorted(self.item_key.items())
        ])
        return ','.join([
            self.region,
            self.table_name,
            key,
        ])

    def attributes(self):
        return {}

    def create(self):
        self.physical_resource_id = NOT_CREATED
        # CloudFormation may call `Delete` after a failed `Create`.
        # delay setting the physical ID until after the PutItem() succeeds

        not_exist_extra_params = {}
        if not self.overwrite:
            # Condition to determine if an object doesn't exist (Key attributes are not set)
            # Note that we never validate that the ItemKey is indeed the table key
            not_exist_extra_params['ConditionExpression'] = " AND ".join([
                f"attribute_not_exists(#{i})"
                for i, k in enumerate(self.item_key.keys())
            ])
            not_exist_extra_params['ExpressionAttributeNames'] = {
                f"#{i}": k
                for i, k in enumerate(self.item_key.keys())
            }

        self.regional_dynamodb_client().put_item(
            TableName=self.table_name,
            Item=self.construct_item(),
            **not_exist_extra_params,
        )  # may raise

        self.physical_resource_id = self.construct_physical_id()
        return self.attributes()

    def update(self):
        new_physical_id = self.construct_physical_id()
        if self.physical_resource_id != new_physical_id:
            return self.create()
            # CloudFormation will call delete() on previous physical_id
        # else:
        self.physical_resource_id = new_physical_id

        self.regional_dynamodb_client().put_item(
            TableName=self.table_name,
            Item=self.construct_item(),
        )  # may raise

        return self.attributes()

    def delete(self):
        if self.physical_resource_id == NOT_CREATED:
            return

        self.regional_dynamodb_client().delete_item(
            TableName=self.table_name,
            Key=self.item_key,
        )


handler = Item.get_handler()
