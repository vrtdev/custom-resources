"""Custom Resources for SSM Parameter Store."""

from troposphere import Tags

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Parameter(LambdaBackedCustomResource):
    """Custom Resource to create or update an SSM Parameter Store parameter."""

    props = {
        'Name': (str, False),
        'Type': (str, False),
        'Description': (str, False),
        'Encoding': (str, False),
        'Value': (str, False),
        'ValueFrom': (str, False),
        'KeyId': (str, False),
        'RandomValue': (dict, False),
        'Tags': (Tags, False),
        'ReturnValue': (bool, False),  # Deprecated
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
        'Names': ([str], True),  # The parameter paths including namespace
        'Serial': (str, False),  # Use this to force an update
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
