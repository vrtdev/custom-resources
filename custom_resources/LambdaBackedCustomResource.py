from six import string_types
from troposphere import iam, Sub, GetAtt
from troposphere.cloudformation import CustomResource


class LambdaBackedCustomResource(CustomResource):
    """
    An generic class to define custom resources.

    If you use this resource you also have to:
     * either add `template.add_resource(LambdaBackedResource.dependencies())` to your code
     * or use split_stacks=True, and import the ServiceToken from another stack (which uses the first option)
    """

    def __init__(self, *args, **kwargs):
        super(LambdaBackedCustomResource, self).__init__(*args, **kwargs)
        if 'ServiceToken' not in self.properties:
            raise ValueError("Error: CustomResource without ServiceToken")

    @classmethod
    def _lambda_policy(cls):
        """
        Return the policy that the lambda function needs to function, if any.

        This should only be the extra permissions. It will already have permissions to write logs
        """
        return None

    @classmethod
    def _update_lambda_settings(cls, settings):
        """
        Update the default settings for the lambda function.

        :param settings: The default settings that will be used
        :return: updated settings
        """
        return settings

    @classmethod
    def lambda_role(cls, role_title):
        policies = [
            iam.Policy(
                PolicyName='WriteLogs',
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                        ],
                        "Resource": "arn:aws:logs:*:*:*",
                    }],
                },
            )
        ]

        # Append specific policy if present
        lambda_policy = cls._lambda_policy()
        if lambda_policy is not None:
            policies.append(iam.Policy(
                PolicyName='CustomResourcePermissions',
                PolicyDocument=lambda_policy,
            ))

        return iam.Role(
                role_title,
                Path='/cfn-lambda/',
                AssumeRolePolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com",
                        },
                        "Action": "sts:AssumeRole",
                    }],
                },
                Policies=policies,
            )

    @classmethod
    def function_settings(cls):
        default_settings = {
            'Description': Sub('{name} - ${{AWS::StackName}}'.format(name=cls.resource_type)),
            'Handler': 'index.handler',
            'Runtime': 'python3.6',
        }
        settings = cls._update_lambda_settings(default_settings)
        return settings
