"""
Custom Resource for managing OpenSearch Service VPC Endpoints.

Uses the opensearch boto3 client to create/update/delete VPC endpoints,
since CloudFormation only supports this natively for OpenSearch Serverless.

Properties:
    DomainArn: ARN of the OpenSearch domain
    SubnetIds: list of subnet IDs for the VPC endpoint
    SecurityGroupIds: list of security group IDs for the VPC endpoint

Attributes:
    VpcEndpointId: The ID of the created VPC endpoint
    Endpoint: The OpenSearch endpoint URL accessible via the VPC endpoint
"""

import time
import structlog

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME

structlog.configure(processors=[structlog.processors.JSONRenderer()])
log = structlog.get_logger()
POLL_INTERVAL_SECONDS = 10


class OpenSearchVPCEndpoint(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use VpcEndpointId as physical ID

    def validate(self):
        self.domain_arn = self.resource_properties.get('DomainArn')
        self.subnet_ids = self.resource_properties.get('SubnetIds', [])
        self.security_group_ids = self.resource_properties.get('SecurityGroupIds', [])

        if not self.domain_arn:
            raise ValueError("DomainArn is required")
        if not self.subnet_ids:
            raise ValueError("SubnetIds is required")
        if not self.security_group_ids:
            raise ValueError("SecurityGroupIds is required")

    def _build_vpc_options(self) -> dict:
        return {
            'SubnetIds': self.subnet_ids,
            'SecurityGroupIds': self.security_group_ids,
        }

    def _get_attributes(self, client) -> dict:
        endpoint_url = ''
        # The VPC endpoint is created asynchronously and the DNS endpoint URL is only
        # available once the status reaches 'ACTIVE'. We poll to ensure dependent
        # resources receive a valid URL.
        while True:
            response = client.describe_vpc_endpoints(
                VpcEndpointIds=[self.physical_resource_id],
            )
            endpoints = response.get('VpcEndpoints', [])
            if not endpoints:
                raise RuntimeError(f"VPC Endpoint {self.physical_resource_id} not found")

            endpoint = endpoints[0]
            status = endpoint.get('Status')
            log.msg("VPC endpoint status", status=status, vpc_endpoint_id=self.physical_resource_id)

            if status == 'ACTIVE':
                endpoint_url = endpoint.get('Endpoint', '')
                break

            if 'FAILED' in status:
                raise RuntimeError(f"VPC Endpoint operation failed with status: {status}")

            if self.context.get_remaining_time_in_millis() < POLL_INTERVAL_SECONDS * 1000 * 2:
                raise RuntimeError("Timeout waiting for VPC Endpoint to become ACTIVE")

            time.sleep(POLL_INTERVAL_SECONDS)

        return {
            'VpcEndpointId': self.physical_resource_id,
            'Endpoint': endpoint_url,
        }

    def create(self):
        client = self.get_boto3_client('opensearch')

        log.msg("Creating OpenSearch VPC endpoint", domain_arn=self.domain_arn)
        response = client.create_vpc_endpoint(
            DomainArn=self.domain_arn,
            VpcOptions=self._build_vpc_options(),
        )

        self.physical_resource_id = response['VpcEndpoint']['VpcEndpointId']
        log.msg("Created VPC endpoint", vpc_endpoint_id=self.physical_resource_id)

        return self._get_attributes(client)

    def update(self):
        client = self.get_boto3_client('opensearch')

        log.msg("Updating OpenSearch VPC endpoint", vpc_endpoint_id=self.physical_resource_id)
        client.update_vpc_endpoint(
            VpcEndpointId=self.physical_resource_id,
            VpcOptions=self._build_vpc_options(),
        )

        return self._get_attributes(client)

    def delete(self):
        client = self.get_boto3_client('opensearch')

        log.msg("Deleting OpenSearch VPC endpoint", vpc_endpoint_id=self.physical_resource_id)
        try:
            client.delete_vpc_endpoint(VpcEndpointId=self.physical_resource_id)
        except client.exceptions.ResourceNotFoundException:
            log.msg("VPC endpoint already deleted", vpc_endpoint_id=self.physical_resource_id)


handler = OpenSearchVPCEndpoint.get_handler()
