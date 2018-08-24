from .dynamodb import JoinGlobalTable


# Backward compatibility
class DynamoDbJoinGlobalTable(JoinGlobalTable):
    _deprecated = 1535105258
    _deprecated_message = 'Use custom_resources.dynamodb.JoinGlobalTable() instead'
