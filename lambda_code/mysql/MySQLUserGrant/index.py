"""MySQLUserGrant custom resource.

MySQLUserGrant custom resource lambda grants privileges to MySQL user accounts. 
"""

from hashlib import sha1
import mysql.connector
from botocore.exceptions import ClientError
from distutils.util import strtobool

from cfn_custom_resource import CloudFormationCustomResource

try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'

NOT_CREATED = "NOT CREATED"

class MySQLUserGrant(CloudFormationCustomResource):
    """
    mysql.MySQLUserGrant.

    Properties:
        Grant: List[str]: the privileges to grant.
        On: str: the privilege level to grant, use *.* for global grants. Update requires replacement.
        User: str: the user to grant, use user@host-syntax. Update requires replacement.
        WithGrantOption: bool: if the user is allows to grant others, defaults to `false`.
        Database: dict: to create the user grant in. Update requires replacement.
            Host: str: the database server is listening on.
            Port: str: port the database server is listening on.
            Database: str: name to connect to.
            User: str: name of the database owner.
            Password: str: to identify the user with.
            PasswordParameterName: str: name of the ssm parameter containing the password of the user.
            PasswordSecretName: str: friendly name or the ARN of the secret in secrets manager containing the password of the user.
    
    Either `Password`, `PasswordParameterName` or `PasswordSecretName` is required.
    """
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def validate(self):
        self.grant = self.resource_properties.get('Grant')
        self.on = self.resource_properties.get('On')
        self.user = self.resource_properties.get('User')
        self.with_grant_option = strtobool(self.resource_properties.get('WithGrantOption', 'false'))
        self.database = self.resource_properties.get('Database')

        if not self.grant:
            return False
        return True

    @property
    def dbowner_password(self):
        db = self.database
        if 'Password' in db:
            return db.get('Password')
        elif 'PasswordParameterName' in db:
            return self.get_ssm_password(db['PasswordParameterName'])
        else:
            return self.get_sm_password(db['PasswordSecretName'])

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.database.get('Host'),
                port=self.database.get('Port'),
                database=self.database.get('DBName'),
                user=self.database.get('User'),
                password=self.dbowner_password,
            )
        except Exception as e:
            raise ValueError('Failed to connect, %s' % e)

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def get_ssm_password(self, name):
        try:
            ssm = self.get_boto3_client('ssm')
            response = ssm.get_parameter(Name=name, WithDecryption=True)
            return response['Parameter']['Value']
        except ClientError as e:
            raise ValueError('Could not obtain password using name {}, {}'.format(name, e))

    def get_sm_password(self, name):
        try:
            secretsmanager = self.get_boto3_client('secretsmanager')
            response = secretsmanager.get_secret_value(SecretId=name)
            return response['SecretString']
        except ClientError as e:
            raise ValueError('Could not obtain password using name {}, {}'.format(name, e))
    
    @property
    def grant_set_old(self):
        return self.get_old('Grant')

    @property
    def grant_level_old(self):
        return self.get_old('On')

    def user_old(self):
        return self.get_old('User')

    @property
    def with_grant_option_old(self):
        return self.get_old('WithGrantOption', False)

    def construct_physical_id(self):
        return "mysql:%s:grants:%s:%s" % (
            self.database.get('DBName'), self.user, self.on)

    def mysql_user(self, user):
        return user.split('@')[0]

    def mysql_user_host(self, user):
        parts = user.split('@')
        return parts[1] if len(parts) > 1 else '%'

    def to_sql_format(self, grants):
        return ','.join(grants)

    def grant_user(self):
        cursor = self.connection.cursor()
        try:
            if self.with_grant_option:
                query = "GRANT %s ON %s TO '%s'@'%s' WITH GRANT OPTION" % (
                    self.to_sql_format(self.grant), self.on,
                    self.mysql_user(self.user), self.mysql_user_host(self.user)
                )
            else:
                query = "GRANT %s ON %s TO '%s'@'%s'" % (
                    self.to_sql_format(self.grant), self.on,
                    self.mysql_user(self.user), self.mysql_user_host(self.user)
                )

            cursor.execute(query)
        finally:
            cursor.close()

    def revoke_user(self):
        cursor = self.connection.cursor()
        try:
            query = "REVOKE %s ON %s FROM '%s'@'%s'" % (
                self.to_sql_format(self.grant), self.on,
                self.mysql_user(self.user), self.mysql_user_host(self.user))
            cursor.execute(query)
        finally:
            cursor.close()

    def revoke_user_old(self):
        cursor = self.connection.cursor()
        try:
            query = "REVOKE %s ON %s FROM '%s'@'%s'" % (
                self.to_sql_format(self.grant_set_old), self.grant_level_old,
                self.mysql_user(self.user_old), self.mysql_user_host(self.user_old))
            cursor.execute(query)
        finally:
            cursor.close()

    def create(self):
        self.physical_resource_id = NOT_CREATED
        try:
            self.connect()
            self.grant_user()
            self.physical_resource_id = self.construct_physical_id()
        except Exception as e:
            self.physical_resource_id = NOT_CREATED
            self.fail('Failed to grant user, %s' % e)
        finally:
            self.close()

    def update(self):
        new_physical_id = self.construct_physical_id()
        if self.physical_resource_id != new_physical_id:
            return self.create()
        self.physical_resource_id = new_physical_id

        try:
            self.connect()
            self.revoke_user_old()
            self.grant_user()
        except Exception as e:
            self.fail('Failed to grant the user, %s' % e)
        finally:
            self.close()

    def delete(self):
        if self.physical_resource_id == NOT_CREATED:
            return

        try:
            self.connect()
            self.revoke_user()
        except Exception as e:
            return self.fail('Failed to revoke the user grant, %s' % e)
        finally:
            self.close()


handler = MySQLUserGrant.get_handler()
