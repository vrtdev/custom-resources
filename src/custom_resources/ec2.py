from .LambdaBackedCustomResource import LambdaBackedCustomResource


class FindAmi(LambdaBackedCustomResource):
    props = {
        'Region': (str, False),  # Default: current region
        'Name': (str, True),  # Like: "amzn-ami-minimal-hvm*"
        'OwnerAlias': (str, False),
        'OwnerId': (str, False),
        'Architecture': (str, False),  # Defaults to: "x86_64",
        'DeviceType': (str, False),  # Defaults to: "ebs",
        'VirtualizationType': (str, False),  # Defaults to: "hvm",
        'State': (str, False),  # Defaults to: 'available',
        'Dummy': (str, False),  # Dummy parameter to trigger updates
    }

    @classmethod
    def _update_lambda_settings(cls, settings):
        # Although I don't understand why, this Lambda sometimes needs more than 3 seconds to run
        settings['Timeout'] = 30
        return settings

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeImages",
                ],
                "Resource": "*",
            }],
        }

    @classmethod
    def name(cls):
        """
        :rtype: List[str]
        """
        # Keep legacy non-structured name for backward compatibility
        return ['Ec2FindAmi']


class StartedWaiter(LambdaBackedCustomResource):
    props = {
        'InstanceIds': ((str, list), True),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstanceStatus",
                ],
                "Resource": "*",
            }],
        }

    @classmethod
    def _update_lambda_settings(cls, settings):
        """
        Update the default settings for the lambda function.

        :param settings: The default settings that will be used
        :return: updated settings
        """
        settings['Timeout'] = 300  # We synchronously wait for EC2's to boot; need more than the default 3 seconds
        return settings
