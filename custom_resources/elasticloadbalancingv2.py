from six import string_types

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class NlbSourceIps(LambdaBackedCustomResource):
    """
    Gets the source IPs of the given Network Load Balancer

    Return Attributes:
        "IPv4Addresses": ["192.0.2.1", "192.0.2.2"]
    """
    props = {
        'LoadBalancerArn': (string_types, True),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "elasticloadbalancing:DescribeLoadBalancers",
                    # DNS requests (no permissions required)
                    "ec2:DescribeNetworkInterfaces",
                ],
                "Resource": "*",
            }],
        }
