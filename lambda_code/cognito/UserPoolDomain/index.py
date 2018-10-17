import os
import random
import string

from cfn_custom_resource import CloudFormationCustomResource
try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'


REGION = os.environ['AWS_REGION']


def split_resource_id(resource_id):
    parts = resource_id.split('/')
    user_pool_id = '/'.join(parts[0:-1])
    domain = parts[-1]

    return user_pool_id, domain


def generate_random_domain_label():
    # Requirement: ^[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?$
    # We're making it easier to just omit the `-`
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))


class UserPoolDomain(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Use `{client_pool_id}/{domain}` instead

    def validate(self):
        try:
            self.user_pool_id = self.resource_properties['UserPoolId']
            self.domain = self.resource_properties.get('Domain', None)

            return True

        except (AttributeError, KeyError):
            return False

    def try_domain(self, domain_name):
        self.get_boto3_client('cognito-idp').create_user_pool_domain(
            UserPoolId=self.user_pool_id,
            Domain=domain_name,
        )

    def create(self):
        if self.domain is not None:
            domain = self.domain
            self.try_domain(domain)
        else:
            attempt = 0
            while attempt < 10:
                domain = generate_random_domain_label()
                try:
                    self.try_domain(domain)
                    break
                except self.get_boto3_client('cognito-idp').exceptions.InvalidParameterException:
                    # Domain already exists
                    pass

        self.physical_resource_id = '/'.join([self.user_pool_id, domain])
        return {
            'Domain': domain,
        }

    def update(self):
        if self.has_property_changed('UserPoolId') or \
                self.has_property_changed('Domain'):
            return self.create()
            # Delete will be done by cloudformation in the Cleanup phase
        else:
            _user_pool_id, domain = split_resource_id(self.physical_resource_id)
            return {
                'Domain': domain,
            }

    def delete(self):
        user_pool_id, domain = split_resource_id(self.physical_resource_id)

        boto_client = self.get_boto3_client('cognito-idp')
        try:
            boto_client.delete_user_pool_domain(
                UserPoolId=user_pool_id,
                Domain=domain,
            )
        except (boto_client.exceptions.ResourceNotFoundException,
                boto_client.exceptions.InvalidParameterException):
            # Assume already deleted
            pass


handler = UserPoolDomain.get_handler()
