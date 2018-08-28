from .ssm import Parameter


# Backward compatibility
class SsmParameter(Parameter):
    _deprecated = 1535105258
    _deprecated_message = 'Use custom_resources.ssm.Parameter() instead'
