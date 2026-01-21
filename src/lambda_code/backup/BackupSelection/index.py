import os

from cfn_custom_resource import CloudFormationCustomResource
try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'


REGION = os.environ['AWS_REGION']


class BackupPlan(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use SelectionId instead

    def validate(self):
        self.backup_plan_id = self.resource_properties['BackupPlanId']
        self.backup_selection = self.resource_properties['BackupSelection']

    def create(self):
        bu = self.get_boto3_client('backup')

        params = {
            'BackupPlanId': self.backup_plan_id,
            'BackupSelection': self.backup_selection,
        }

        resp = bu.create_backup_selection(**params)

        self.physical_resource_id = resp['SelectionId']

        return {}

    def update(self):
        # backupselection doesn't have a put or update, but since the function below results in a different
        # physical id, cloudformation knows to delete the original...

        return self.create()

    def delete(self):
        bu = self.get_boto3_client('backup')
        try:
            bu.delete_backup_selection(BackupPlanId=self.backup_plan_id, SelectionId=self.physical_resource_id)
        except (bu.exceptions.ResourceNotFoundException,
                bu.exceptions.InvalidParameterException):
            # Assume already deleted
            pass


handler = BackupPlan.get_handler()
