"""Custom Resources for SSM Parameter Store."""

from six import string_types
from troposphere import Tags

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Parameter(LambdaBackedCustomResource):
    """Custom Resource to create or update an SSM Parameter Store parameter."""

    props = {
        'Name': (string_types, False),
        'Type': (string_types, False),
        'Description': (string_types, False),
        'Encoding': (string_types, False),
        'Value': (string_types, False),
        'ValueFrom': (string_types, False),
        'KeyId': (string_types, False),
        'RandomValue': (dict, False),
        'Tags': (Tags, False),
        'ReturnValue': (bool, False),
        'ReturnValueHash': (bool, False),
    }

    def validate(self):
        """Validate the properties of the resource."""
        # ValueFrom, Value and RandomValue are mutually exclusive: XOR their presence
        if bool('Value' in self.properties) ^ bool('ValueFrom' in self.properties) ^ bool('RandomValue' in self.properties):
            pass  # Good, either Value, ValueFrom or RandomValue provided
        else:
            raise TypeError(f"{self.__class__.__name__}: Value, ValueFrom and RandomValue are mutually exclusive")

    @classmethod
    def _update_lambda_settings(cls, settings):
        """Update the CloudFormation configuration for the lambda function."""
        settings['Runtime'] = 'python3.12'
        return settings

    @classmethod
    def _lambda_policy(cls) -> dict:
        """Return the policy that the lambda function needs to function."""
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "ssm:PutParameter",
                    "ssm:GetParameters",
                    "ssm:DeleteParameter",
                    "ssm:AddTagsToResource",
                    "ssm:RemoveTagsFromResource",
                    "ssm:GetParameter",
                    "secretsmanager:GetSecretValue",
                ],
                "Resource": "*",
            }],
        }

    @classmethod
    def name(cls) -> list[str]:
        """Return the logical resource ID of the Lambda function."""
        # Keep legacy non-structured name for backward compatibility
        return ['SsmParameter']


class ParseDict(LambdaBackedCustomResource):
    """Custom Resource to parse a dictionary from SSM Parameter Store."""

    props = {
        'Names': ([string_types], True),  # The parameter paths including namespace
        'Serial': (string_types, False),  # Use this to force an update
    }

    @classmethod
    def _lambda_policy(cls) -> dict:
        """Return the policy that the lambda function needs to function."""
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameters",
                ],
                "Resource": "*",
            }],
        }

    @classmethod
    def name(cls) -> list[str]:
        """Return the logical resource ID of the Lambda function."""
        # Avoid Injecting `0` in name by setting it statically
        return ['SsmParseDict']
