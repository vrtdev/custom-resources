from .cognito import UserPoolClient


# Backward compatibility
class CognitoUserPoolClient(UserPoolClient):
    _deprecated = 1535105258
    _deprecated_message = 'Use custom_resources.cognito.UserPoolClient() instead'
