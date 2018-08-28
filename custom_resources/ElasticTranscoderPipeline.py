from .elastictranscoder import Pipeline

# Backward compatibility
class ElasticTranscoderPipeline(Pipeline):
    _deprecated = 1535105258
    _deprecated_message = 'Use custom_resources.elastictranscoder.Pipeline() instead'
