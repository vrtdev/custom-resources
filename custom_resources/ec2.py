from six import string_types

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class FindAmi(LambdaBackedCustomResource):
    props = {
        'Region': (string_types, False),  # Default: current region
        'Name': (string_types, True),  # Like: "amzn-ami-minimal-hvm*"
        'OwnerAlias': (string_types, False),
        'OwnerId': (string_types, False),
        'Architecture': (string_types, False),  # Defaults to: "x86_64",
        'DeviceType': (string_types, False),  # Defaults to: "ebs",
        'VirtualizationType': (string_types, False),  # Defaults to: "hvm",
        'State': (string_types, False),  # Defaults to: 'available',
        'Dummy': (string_types, False),  # Dummy parameter to trigger updates
    }

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
