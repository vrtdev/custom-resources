"""
Custom resource to create an ingest pipeline in your AWS Elasticsearch Cluster.
"""

import json
import os

from cfn_custom_resource import CloudFormationCustomResource
from _metadata import CUSTOM_RESOURCE_NAME

from elasticsearch import Elasticsearch, RequestsHttpConnection, ElasticsearchException
from requests_aws4auth import AWS4Auth

REGION = os.environ['AWS_REGION']

class IngestPipelineViaVpc(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME

    def validate(self):
        self.es_host = self.resource_properties['EsHost']
        self.pipeline_name = self.resource_properties['PipelineName']
        self.ingest_doc = self.resource_properties['IngestDocument']

    def create(self):
        service = 'es'
        credentials = self.get_boto3_session().get_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, service, session_token=credentials.token)

        es = Elasticsearch(
            hosts = [{'host': self.es_host, 'port': 443}],
            http_auth = awsauth,
            use_ssl = True,
            verify_certs = True,
            connection_class = RequestsHttpConnection
        )

        es.ingest.put_pipeline(id=self.pipeline_name, body=json.dumps(self.ingest_doc))
        return {}

    def update(self):
        return self.create()

    def delete(self):
        service = 'es'
        credentials = self.get_boto3_session().get_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, service, session_token=credentials.token)

        es = Elasticsearch(
            hosts = [{'host': self.es_host, 'port': 443}],
            http_auth = awsauth,
            use_ssl = True,
            verify_certs = True,
            connection_class = RequestsHttpConnection
        )

        try:
            es.ingest.delete_pipeline(id=self.pipeline_name)
        except ElasticsearchException:
            # Assume already deleted
            pass


handler = IngestPipelineViaVpc.get_handler()
