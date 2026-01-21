import json

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

        resource = self.nlb_arn.split(':')[5]
        name = '/'.join(resource.split('/')[1:])
        description = f"ELB {name}"
        print(f"Doing lookup for ENIs with description `{description}`")

        ec2_client = self.get_boto3_client('ec2')
        # Paginator is also available, but use simple client. We are querying on Public IP,
        # so we expect at most a single answer, no pagination issues expected.
        enis = ec2_client.describe_network_interfaces(
            Filters=[{
                'Name': 'description',
                'Values': [description],
            }],
        )
        enis = enis['NetworkInterfaces']
        print(f"Found {len(enis)} ENIs")

        enis = [
            eni
            for eni in enis
            if eni["InterfaceType"] == "network_load_balancer"
            and eni["Attachment"]["InstanceOwnerId"] == "amazon-aws"
        ]
        print(f"Found {len(enis)} ENIs of type network_load_balancer")

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
