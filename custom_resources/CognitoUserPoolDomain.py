from .cognito import UserPoolDomain


# Backward compatibility
class CognitoUserPoolDomain(UserPoolDomain):
    _deprecated = 1535105258
    _deprecated_message = 'Use custom_resources.cognito.UserPoolDomain() instead'
