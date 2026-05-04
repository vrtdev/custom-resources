"""Custom Resource for OpenSearch Service VPC Endpoints."""

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class VPCEndpoint(LambdaBackedCustomResource):
    """Custom Resource to manage an OpenSearch Service VPC Endpoint.

    CloudFormation does not support AWS::OpenSearchService::VPCEndpoint
    for OpenSearch Service domains (only serverless), so we use the
    boto3 opensearch client to manage the lifecycle.
    """

    props = {
        'DomainArn': (str, True),
        'SubnetIds': ([str], True),
        'SecurityGroupIds': ([str], True),
    }

    @classmethod
    def _update_lambda_settings(cls, settings):
        """VPC endpoint creation can take a while for cross-account domains."""
        settings['Timeout'] = 900
        return settings

    @classmethod
    def _lambda_policy(cls) -> dict:
        """Return the policy that the lambda function needs to function."""
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "es:CreateVpcEndpoint",
                    "es:UpdateVpcEndpoint",
                    "es:DeleteVpcEndpoint",
                    "es:DescribeVpcEndpoints",
                    "ec2:CreateVpcEndpoint",
                    "ec2:DescribeVpcEndpoints",
                    "ec2:ModifyVpcEndpoint",
                    "ec2:DeleteVpcEndpoints",
                    "ec2:CreateTags",
                    "ec2:DescribeTags",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeVpcs",
                ],
                "Resource": "*",
            }],
        }
