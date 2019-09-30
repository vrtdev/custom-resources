import json
import traceback

import dns.resolver

from cfn_custom_resource import CloudFormationCustomResource
try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'


def lookup_internal_ipv4(ec2_client, public_ipv4: str) -> str:
    # Paginator is also available, but use simple client. We are querying on Public IP,
    # so we expect at most a single answer, no pagination issues expected.
    eni = ec2_client.describe_network_interfaces(
        Filters=[{
            'Name': 'addresses.association.public-ip',
            'Values': [public_ipv4],
        }],
    )

    return public_ipv4


class NlbSourceIps(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def validate(self):
        self.nlb_arn = self.resource_properties['LoadBalancerArn']

    def create(self):
        print(f"Resolving private IPs for `{self.nlb_arn}`")
        elbv2_client = self.get_boto3_client('elbv2')

        # Paginator is also available, but use simple client. We are querying on ARN, so we expect at most a single
        # answer, no pagination issues expected.
        nlbs = elbv2_client.describe_load_balancers(
            LoadBalancerArns=[
                self.nlb_arn,
            ],
        )

        try:
            nlbs = nlbs['LoadBalancers'][0]
            nlb_dns_name = nlbs['DNSName']
            nlb_scheme = nlbs['Scheme']
            print(f"DNS name: {nlb_dns_name}")
        except IndexError:
            print("Not found")
            raise RuntimeError(f"NLB with ARN `{self.nlb_arn}` not found")
        except KeyError:
            traceback.print_exc()
            raise RuntimeError("Error extracting `DNSName` from DescribeLoadBalancers response")

        a_records = dns.resolver.query(nlb_dns_name, rdtype=dns.rdatatype.A)  # may raise
        ipv4_addresses = {
            str(rr)
            for rr in a_records
        }
        print("Found IP addresses:")
        for a in ipv4_addresses:
            print(a)

        if nlb_scheme == 'internet-facing':
            print("NLB is internet-facing, resolving to internal IPs")
            ec2_client = self.get_boto3_client('ec2')
            # Paginator is also available, but use simple client. We are querying on Public IP,
            # so we expect at most a single answer, no pagination issues expected.
            enis = ec2_client.describe_network_interfaces(
                Filters=[{
                    'Name': 'addresses.association.public-ip',
                    'Values': list(ipv4_addresses),
                }],
            )
            enis = enis['NetworkInterfaces']
            if len(enis) != len(ipv4_addresses):
                print("Warning: did not find all ENIs")

            ipv4_addresses = [
                eni['PrivateIpAddress']
                for eni in enis
            ]
            print("Found internal IP addresses:")
            for a in ipv4_addresses:
                print(a)

        ipv4_addresses = sorted(list(ipv4_addresses))
        attributes = {
            'IPv4Addresses': ipv4_addresses,
        }
        for i, ip in enumerate(ipv4_addresses):
            attributes[f"IPv4Address{i}"] = ip

        print("Returning attributes:")
        print(json.dumps(attributes))
        return attributes

    def update(self):
        return self.create()

    def delete(self):
        pass


handler = NlbSourceIps.get_handler()
