from six import string_types
from troposphere import Tags

from .LambdaBackedCustomResource import LambdaBackedCustomResource


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
        'BackupSelection ': (dict, True),
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
                ],
                "Resource": "*",
            }],
        }

