import os
import re


def test_random_label():
    os.environ['AWS_REGION'] = 'none'
    from ..index import generate_random_domain_label

    label = generate_random_domain_label()
    assert isinstance(label, str)
    assert len(label) > 0
    assert len(label) < 64
    label2 = generate_random_domain_label()
    assert label != label2

    assert re.match(r'^[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?$', label)


def test_split_resourceid():
    os.environ['AWS_REGION'] = 'none'
    from ..index import split_resource_id

    assert split_resource_id('foo/bar/baz') == ('foo/bar', 'baz')
