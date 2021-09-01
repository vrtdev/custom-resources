"""
Custom resource to create an ingest pipeline in your AWS Elasticsearch Cluster.
"""

import json
import requests
from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME


class IngestPipeline(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def validate(self):
        self.es_host = self.resource_properties['EsHost']
        self.pipeline_name = self.resource_properties['PipelineName']
        self.ingest_doc = self.resource_properties['IngestDocument']

    def create(self):
        url = 'https://' + self.es_host + '/_ingest/pipeline/' + self.pipeline_name
        requests.put(url, json.dumps(self.ingest_doc))
        return {}

    def update(self):
        return self.create()

    def delete(self):
        url = 'https://' + self.es_host + '/_ingest/pipeline/' + self.pipeline_name
        try:
            requests.delete(url)
        except (requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects,
                requests.exceptions.RequestException):
            # Assume already deleted
            pass


handler = IngestPipeline.get_handler()
