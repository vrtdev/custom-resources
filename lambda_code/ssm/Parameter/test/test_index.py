import sys
import os

class FakeMetadata:
    CUSTOM_RESOURCE_NAME = 'test'
sys.modules["_metadata"] = FakeMetadata

os.environ['AWS_REGION'] = 'test'

from ..index import Parameter


def test_pass():
    assert True
