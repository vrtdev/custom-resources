import os

from cfn_custom_resource import CloudFormationCustomResource
try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'


REGION = os.environ['AWS_REGION']


class BackupVault(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use BackupVaultName instead

    def validate(self):
        self.backup_vault_name = self.resource_properties['BackupVaultName']
        self.backup_vault_tags = self.resource_properties.get('BackupVaultTags', [])

    def create(self):
        bu = self.get_boto3_client('backup')

        params = {
            'BackupVaultName': self.backup_vault_name,
            'BackupVaultTags': self.backup_vault_tags,
        }

        resp = bu.create_backup_vault(**params)

        self.physical_resource_id = resp['BackupVaultName']

        return {}

    def update(self):
        raise NotImplementedError("Updates not supported")

    def delete(self):
        bu = self.get_boto3_client('backup')
        try:
            bu.delete_backup_vault(BackupVaultName=self.physical_resource_id)
        except (bu.exceptions.ResourceNotFoundException,
                bu.exceptions.InvalidParameterException):
            # Assume already deleted
            pass


handler = BackupVault.get_handler()
