from six import string_types
from troposphere import iam, Sub, ImportValue
from troposphere.cloudformation import CustomResource

from . import _get_custom_resources_stack_name


class LambdaBackedCustomResource(CustomResource):
    """
    An generic class to define custom resources.

    The ServiceToken of the custom resources is retrieved via an ImportValue() call.
    By default, the value is imported as '{stack_name}-{cust_res_name}ServiceToken'.
    You can change the stack_name by overriding custom_resources.CUSTOM_RESOURCES_STACK_NAME before you start.
    """

    def __init__(self, *args, **kwargs):
        name = self.__class__.__module__.split('.')
        name.append(self.__class__.__name__)
        name.pop(0)  # remove `custom_resources` package name
        self.resource_type = "Custom::" + '@'.join(name)
        # '.' is not allowed in a Custom::-name, but `@` is

        if 'ServiceToken' not in self.props:
            self.props['ServiceToken'] = (object, True)  # Anything goes

        if 'ServiceToken' not in kwargs:
            kwargs['ServiceToken'] = self.service_token()

        super(LambdaBackedCustomResource, self).__init__(*args, **kwargs)

        self.check_deprecation()

    def service_token(self):
        return ImportValue(Sub("{custom_resources_stack_name}-{custom_resource_name}ServiceToken".format(
            custom_resources_stack_name=_get_custom_resources_stack_name(),
            custom_resource_name=self.custom_resource_name(self.name())
        )))

    def role(self):
        return ImportValue(Sub("{custom_resources_stack_name}-{custom_resource_name}Role".format(
            custom_resources_stack_name=_get_custom_resources_stack_name(),
            custom_resource_name=self.custom_resource_name(self.name())
        )))

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
