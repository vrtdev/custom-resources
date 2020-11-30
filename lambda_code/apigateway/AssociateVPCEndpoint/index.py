import typing

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


class AssociateVPCEndpoint(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use version ARN instead

    def validate(self):
        self.rest_api_id: str = self.resource_properties['RestApiId']
        self.vpc_endpoint_id: str = self.resource_properties['VpcEndpointId']

    def get_attributes(self):
        return {}

    def create(self):
        self.physical_resource_id = self.rest_api_id + '/' + self.vpc_endpoint_id

        client = self.get_boto3_client('apigateway')
        response = client.update_rest_api(
            restApiId=self.rest_api_id,
            patchOperations=[
                {
                    'op': 'add',
                    'path': '/endpointConfiguration/vpcEndpointIds',
                    'value': self.vpc_endpoint_id,
                },
            ]
        )

        return self.get_attributes()

    def update(self):
        if self.has_property_changed('RestApiId') or \
                self.has_property_changed('VpcEndpointId'):
            return self.create()
            # CloudFormation will call delete() on the old resource
        else:
            # Nothing changed, nothing to do
            return self.get_attributes()

    def delete(self):
        client = self.get_boto3_client('apigateway')
        response = client.update_rest_api(
            restApiId=self.rest_api_id,
            patchOperations=[
                {
                    'op': 'remove',
                    'path': '/endpointConfiguration/vpcEndpointIds',
                    'value': self.vpc_endpoint_id,
                },
            ]
        )


handler = AssociateVPCEndpoint.get_handler()
