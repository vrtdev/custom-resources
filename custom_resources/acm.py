from six import string_types
from troposphere import Tags

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class DnsValidatedCertificate(LambdaBackedCustomResource):
    props = {
        'DomainName': (string_types, True),
        'SubjectAlternativeNames': ([string_types], False),
        'Region': (string_types, False),  # Default: current region
        'Tags': (Tags, False),
    }

    @classmethod
    def _update_lambda_settings(cls, settings):
        # It can take a while before the DNS-entries are generated and visible
        settings['Timeout'] = 300
        return settings

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "acm:DeleteCertificate",
                    "acm:RequestCertificate",
                    "acm:DescribeCertificate",
                    "acm:AddTagsToCertificate",
                    "acm:ListTagsForCertificate",
                    "acm:RemoveTagsFromCertificate",
                    "cloudformation:DescribeStacks",  # Read tags
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
        return ['AcmDnsValidatedCertificate']
