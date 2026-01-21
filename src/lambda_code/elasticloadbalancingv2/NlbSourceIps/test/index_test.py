import datetime
import typing

import pytest
import mock
from dateutil.tz import tzutc

from .. import index


@pytest.fixture()
def nlb_arn_gen():
    def gen(
        region: str = 'eu-west-1',
        account_id: str = '123456789012',
        name: str = 'example-nlb',
        hex_id: str = '10fc507b754aa253',
    ):
        return f"arn:aws:elasticloadbalancing:{region}:{account_id}:loadbalancer/net/{name}/{hex_id}"
    return gen


def describe_load_balancers(
        arn: str = 'arn:aws:elasticloadbalancing:eu-west-1:123456789012:loadbalancer/net/example/20fc5ff6294aa253',
        scheme: str = 'internet-facing',
        vpc: str = 'vpc-12345678',
        zones_subnetid: typing.Mapping[str, str] = None,
):
    if zones_subnetid is None:
        zones_subnetid = {
            'eu-west-1a': 'subnet-12345678',
            'eu-west-1c': 'subnet-78901234',
        }

    _, _, _, region, account_id, arn5 = arn.split(':')
    lb, net, name, hex_id = arn5.split('/')
    assert lb == 'loadbalancer'
    assert net == 'net'

    return {
        'LoadBalancers': [
            {
                'LoadBalancerArn': arn,
                'DNSName': f'{name}-{hex_id}.elb.{region}.amazonaws.com',
                'CanonicalHostedZoneId': 'Z2IFOLAFXWLO4F',
                'CreatedTime': datetime.datetime(2019, 9, 26, 9, 36, 25, 677000, tzinfo=tzutc()),
                'LoadBalancerName': name,
                'Scheme': scheme,
                'VpcId': vpc,
                'State': {'Code': 'active'},
                'Type': 'network',
                'AvailabilityZones': [
                    {
                        'ZoneName': zone,
                        'SubnetId': subnet_id,
                    }
                    for zone, subnet_id in zones_subnetid.items()
                ],
                'IpAddressType': 'ipv4'
            }
        ],
        'ResponseMetadata': {
            'RequestId': '598c1aa9-2749-4fef-a5ec-9c3dda0e7176',
            'HTTPStatusCode': 200,
            'HTTPHeaders': {
                'x-amzn-requestid': '598c1aa9-2749-4fef-a5ec-9c3dda0e7176',
                'content-type': 'text/xml',
                'content-length': '42',
                'date': 'Thu, 26 Sep 2019 12:02:30 GMT'
            },
            'RetryAttempts': 0
        }
    }


def describe_network_interfaces(
        ips: typing.Mapping[str, str] = None,
):
    if ips is None:
        ips = {
            '198.51.100.10': '192.0.2.1',
            '198.51.100.20': '192.0.2.2',
        }

    def network_interface(
            public_ip: str = '198.51.100.10',
            private_ip: str = '192.0.2.1',
    ):
        dashed_public_ip = public_ip.replace('.', '-')
        dashed_private_ip = private_ip.replace('.', '-')
        return {
            'Association': {
                'IpOwnerId': '560488543506',
                'PublicDnsName': f'ec2-{dashed_public_ip}.eu-west-1.compute.amazonaws.com',
                'PublicIp': public_ip
            },
            'Attachment': {
                'AttachmentId': 'ela-attach-ab751b96',
                'DeleteOnTermination': False,
                'DeviceIndex': 1,
                'InstanceOwnerId': 'amazon-aws',
                'Status': 'attached'
            },
            'AvailabilityZone': 'eu-west-1c',
            'Description': 'ELB net/test/10dc5ff7754aa253',
            'Groups': [],
            'InterfaceType': 'network_load_balancer',
            'Ipv6Addresses': [
                {
                    'Ipv6Address': '2a05:d018:704:4105:a23c:c62b:542d:30ea'
                }
            ],
            'MacAddress': '0a:84:4b:dc:f1:d8',
            'NetworkInterfaceId': 'eni-028faeb801567b1ed',
            'OwnerId': '123456789012',
            'PrivateDnsName': f'ip-{dashed_private_ip}.eu-west-1.compute.internal',
            'PrivateIpAddress': private_ip,
            'PrivateIpAddresses': [
                {
                    'Association': {
                        'IpOwnerId': '560488543506',
                        'PublicDnsName': f'ec2-{dashed_public_ip}.eu-west-1.compute.amazonaws.com',
                        'PublicIp': public_ip
                    },
                    'Primary': True,
                    'PrivateDnsName': f'ip-{dashed_private_ip}.eu-west-1.compute.internal',
                    'PrivateIpAddress': private_ip
                }
            ],
            'RequesterId': '560488543506',
            'RequesterManaged': True,
            'SourceDestCheck': False,
            'Status': 'in-use',
            'SubnetId': 'subnet-48e4b010',
            'TagSet': [],
            'VpcId': 'vpc-d7685ff3'
        }

    return {
        'NetworkInterfaces': [
            network_interface(public_ip, private_ip)
            for public_ip, private_ip in ips.items()
        ],
        'ResponseMetadata': {
            'RequestId': '39231250-5727-4e08-b734-af97e5b55ba3',
            'HTTPStatusCode': 200,
            'HTTPHeaders': {
                'content-type': 'text/xml;charset=UTF-8',
                'content-length': '2674',
                'vary': 'accept-encoding',
                'date': 'Thu, 26 Sep 2019 13:13:53 GMT',
                'server': 'AmazonEC2'
            },
            'RetryAttempts': 0
        }
    }


def test_nlb_source_ips(nlb_arn_gen):
    name = "test-nlb"
    hex_id = "12345678"
    nlb_arn = nlb_arn_gen(name=name, hex_id=hex_id)

    o = index.NlbSourceIps()
    o.nlb_arn = nlb_arn

    ips = {
        '198.51.100.10': '192.0.2.1',
        '198.51.100.20': '192.0.2.2',
    }
    def describe_eni(*args, **kwargs):
        assert len(args) == 0
        filters = kwargs.pop('Filters')
        assert len(kwargs) == 0
        assert len(filters) == 1
        assert filters[0]['Name'] == 'description'
        assert filters[0]['Values'] == [f"ELB net/{name}/{hex_id}"]
        return describe_network_interfaces({
            k: v
            for k, v in ips.items()
        })
    ec2_client = mock.Mock(describe_network_interfaces=describe_eni)
    o.BOTO3_CLIENTS['ec2'] = ec2_client

    attributes = o.create()

    returned_ips = attributes['IPv4Addresses']
    for ip in ips.values():
        assert ip in returned_ips

    for i, ip in enumerate(returned_ips, start=0):
        assert attributes[f"IPv4Address{i}"] in returned_ips
