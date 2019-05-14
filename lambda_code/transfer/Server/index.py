from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME

API_GATEWAY_IDENTITY_PROVIDER = 'API_GATEWAY'

VPC_ENDPOINT_TYPE = 'VPC_ENDPOINT'

SERVICE_IDENTITY_PROVIDER_TYPE = 'SERVICE_MANAGED'
PUBLIC_ENDPOINT_TYPE = 'PUBLIC'


class Server(CloudFormationCustomResource):
    """
    Properties:
        EndpointType: str: endpoint type (PUBLIC or VPC_ENDPOINT, default is PUBLIC)
        EndpointDetails: dict: endpoint details, only needed for VPC_ENDPOINT type
        IdentityProviderType: str: identity provider type (SERVICE_MANAGED or API_GATEWAY, default is SERVICE_MANAGED)
        IdentityProviderDetails: dict: identity provider details, only needed for API_GATEWAY provider type
        HostKey: str: hostkey: private key
        LoggingRole: str: logging role: role for logging access to server
    """
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use Server Id instead

    def validate(self):
        self.endpoint_type = self.resource_properties.get('EndpointType', PUBLIC_ENDPOINT_TYPE)
        self.endpoint_details = self.resource_properties.get('EndpointDetails')
        self.identity_provider_type = self.resource_properties.get('IdentityProviderType', SERVICE_IDENTITY_PROVIDER_TYPE)
        self.identity_provider_details = self.resource_properties.get('IdentityProviderDetails')
        self.hostkey = self.resource_properties.get('HostKey')
        self.logging_role = self.resource_properties.get('LoggingRole')

        if VPC_ENDPOINT_TYPE == self.endpoint_type and self.endpoint_details is None:
            raise ValueError('{} type specified without endpoint details'.format(VPC_ENDPOINT_TYPE))

        if PUBLIC_ENDPOINT_TYPE == self.endpoint_type and self.endpoint_details is not None:
            raise ValueError('{} type specified *with* endpoint details'.format(PUBLIC_ENDPOINT_TYPE))

        if API_GATEWAY_IDENTITY_PROVIDER == self.identity_provider_type and self.identity_provider_details is None:
            raise ValueError('{} type specified without identity provider details'.format(API_GATEWAY_IDENTITY_PROVIDER))

        if SERVICE_IDENTITY_PROVIDER_TYPE == self.identity_provider_type and self.identity_provider_details is not None:
            raise ValueError('{} type specified *with* identity provider details'.format(SERVICE_IDENTITY_PROVIDER_TYPE))

    @staticmethod
    def add_if_not_none(params, key, value):
        if value is not None:
            params[key] = value

    def build_params(self):
        required = {
            'EndpointType': self.endpoint_type,
            'IdentityProviderType': self.identity_provider_type
        }
        self.add_if_not_none(required, 'EndpointDetails', self.endpoint_details)
        self.add_if_not_none(required, 'IdentityProviderDetails', self.identity_provider_details)
        self.add_if_not_none(required, 'HostKey', self.hostkey)
        self.add_if_not_none(required, 'LoggingRole', self.logging_role)

        return required

    def get_attributes(self):
        return {'ServerId': self.physical_resource_id}

    def create(self):
        transfer_client = self.get_boto3_client('transfer')

        params = self.build_params()
        response = transfer_client.create_server(**params)
        self.physical_resource_id = response['ServerId']

        return self.get_attributes()

    def update(self):
        transfer_client = self.get_boto3_client('transfer')

        params = self.build_params()
        params['ServerId'] = self.physical_resource_id
        transfer_client.update_server(**params)

        return self.get_attributes()

    def delete(self):
        transfer_client = self.get_boto3_client('transfer')

        transfer_client.delete_server(ServerId=self.physical_resource_id)


handler = Server.get_handler()
