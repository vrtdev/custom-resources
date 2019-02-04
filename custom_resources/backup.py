from six import string_types
from troposphere import Tags

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class BackupVault(LambdaBackedCustomResource):
    props = {
        'BackupVaultName': (string_types, True),
        'BackupVaultTags': (dict, True),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "backup:CreateBackupVault",
                    "backup:DeleteBackupVault",
                    "backup-storage:MountCapsule",
                    "backup:DeleteBackupVaultAccessPolicy",
                    "backup:DeleteBackupVaultNotification",
                    "kms:CreateGrant",
                    "kms:GenerateDataKey",
                    "kms:Decrypt",
                    "kms:RetireGrant",
                    "kms:DescribeKey",
                ],
                "Resource": "*",
            }],
        }


class BackupPlan(LambdaBackedCustomResource):
    props = {
        'BackupPlan': (dict, True),
        'BackupPlanTags ': (Tags, False),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "backup:CreateBackupPlan",
                    "backup:DeleteBackupPlan",
                    "backup:UpdateBackupPlan",
                ],
                "Resource": "*",
            }],
        }


class BackupSelection(LambdaBackedCustomResource):
    props = {
        'BackupPlanId': (string_types, True),
        'BackupSelection': (dict, True),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "backup:CreateBackupSelection",
                    "backup:DeleteBackupSelection",
                    "iam:PassRole",
                ],
                "Resource": "*",
            }],
        }
