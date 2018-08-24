from .awslambda import Version


# Backward compatibility
class LambdaVersion(Version):
    _deprecated = 1535105258
    _deprecated_message = 'Use custom_resources.awslambda.Version() instead'
