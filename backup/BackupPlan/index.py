import os

from cfn_custom_resource import CloudFormationCustomResource
try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'


REGION = os.environ['AWS_REGION']


class BackupPlan(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use BackupPlanId instead

    def validate(self):
        self.backup_plan = self.resource_properties['BackupPlan']
        self.backup_plan_tags = self.resource_properties.get('BackupPlanTags', [])



    def create(self):
        bu = self.get_boto3_client('backup')

        params = {
            'BackupPlan': self.backup_plan,
            'BackupPlanTags': self.backup_plan_tags,
        }

        resp = bu.create_backup_plan(**params)

        self.physical_resource_id = resp['BackupPlanId']

        return {}

    def update(self):
        bu = self.get_boto3_client('backup')

        params = {
            'BackupPlanId': self.physical_resource_id,
            'BackupPlan': self.backup_plan
        }

        resp = bu.update_backup_plan(**params)

        return {}

    def delete(self):
        bu = self.get_boto3_client('backup')
        try:
            bu.delete_backup_plan(BackupPlanId=self.physical_resource_id)
        except (bu.exceptions.ResourceNotFoundException,
                bu.exceptions.InvalidParameterException):
            # Assume already deleted
            pass


handler = BackupPlan.get_handler()
