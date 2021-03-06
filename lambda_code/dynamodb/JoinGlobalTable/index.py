"""
Custom Resource for joining up DynamoDB tables in to a Global Table.

Parameters:
 * TableName: required: name of the tables to join.

Requirements:
 * All tables must share the same name and have Streams enabled (cfr AWS documentation)
"""

import os

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


REGION = os.environ['AWS_REGION']


class JoinGlobalTable(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use ARN of global table instead

    def validate(self):
        try:
            self.table_name = self.resource_properties.pop('TableName')

            if len(self.resource_properties) > 0:
                return False
            return True
        except KeyError:
            return False

    def create(self):
        boto_client = self.get_boto3_client('dynamodb')
        try:
            print(f"Trying to create global table {self.table_name}")
            global_table = boto_client.create_global_table(
                GlobalTableName=self.table_name,
                ReplicationGroup=[
                    {'RegionName': REGION}
                ],
            )
            print("done")

        except boto_client.exceptions.GlobalTableAlreadyExistsException:
            try:
                print("Global table already exists, trying to join this region to the global table")
                global_table = boto_client.update_global_table(
                    GlobalTableName=self.table_name,
                    ReplicaUpdates=[
                        {'Create': {'RegionName': REGION}}
                    ],
                )
                print("done")
            except boto_client.exceptions.ReplicaAlreadyExistsException:
                raise RuntimeError("This region is already joined to the GlobalTable. "
                                   "Not taking ownership of this Join.")

        self.physical_resource_id = global_table['GlobalTableDescription']['GlobalTableArn']
        print(f"GlobalTableArn: {self.physical_resource_id}")

        return {}

    def update(self):
        if self.has_property_changed('TableName'):
            # We need a new GlobalTable, switch to create and let CLEANUP delete the old one
            return self.create()

        # Nothing else can change
        # Ignore request succesfully
        print("Ignoring update")
        return {}

    def delete(self):
        boto_client = self.get_boto3_client('dynamodb')
        try:
            print("Trying to delete global table {self.table_name}")
            boto_client.update_global_table(
                GlobalTableName=self.table_name,
                ReplicaUpdates=[
                    {'Delete': {'RegionName': REGION}}
                ],
            )
            print("done")
        except boto_client.exceptions.GlobalTableNotFoundException:
            print("Delete failed, assuming success...")


handler = JoinGlobalTable.get_handler()
