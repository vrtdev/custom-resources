import time
import warnings

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
    _deprecated = False  # Unix epoch time (integer) of deprecation
    _deprecated_message = ''  # arbitrary string explaining the upgrade path

    def __init__(self, *args, **kwargs):
        self.resource_type = "Custom::" + self.custom_resource_name(self.name())

        if 'ServiceToken' not in self.props:
            self.props['ServiceToken'] = (object, True)  # Anything goes

        if 'ServiceToken' not in kwargs:
            kwargs['ServiceToken'] = self.service_token()

        super(LambdaBackedCustomResource, self).__init__(*args, **kwargs)

        self.check_deprecation(stacklevel=2)

    def service_token(self):
        return ImportValue(Sub("{custom_resources_stack_name}-{custom_resource_name}ServiceToken".format(
            custom_resources_stack_name=_get_custom_resources_stack_name(),
            custom_resource_name=self.cloudformation_name(self.name())
        )))

    def role(self):
        return ImportValue(Sub("{custom_resources_stack_name}-{custom_resource_name}Role".format(
            custom_resources_stack_name=_get_custom_resources_stack_name(),
            custom_resource_name=self.cloudformation_name(self.name())
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

    @classmethod
    def check_deprecation(cls, stacklevel=1):
        if not cls._deprecated:
            return
        warnings.warn(
            "{c} is deprecated since {t}\n{m}".format(
                c=cls.__name__,
                t=time.strftime('%Y-%m-%d', time.localtime(cls._deprecated)),
                m=cls._deprecated_message,
            ),
            DeprecationWarning,
            stacklevel=stacklevel+1,
        )
        # Sleep for 1 second for every day since this was deprecated
        time.sleep((time.time() - cls._deprecated) / 86400)

    @classmethod
    def name(cls):
        """
        :rtype: List[str]
        """
        name = cls.__module__.split('.')
        name.pop(0)  # remove `custom_resources` package name
        name.append(cls.__name__)
        return name

    @staticmethod
    def cloudformation_name(name):
        """
        :type name: List[str]
        :rtype: str
        """
        return '0'.join(name)
        # '.' is not allowed...

    @staticmethod
    def custom_resource_name(name):
        """
        :type name: List[str
        :rtype: str
        """
        return '@'.join(name)
        # '.' is not allowed in a Custom::-name, but `@` is
