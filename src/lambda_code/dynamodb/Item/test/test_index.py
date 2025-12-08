import os
os.environ['AWS_REGION'] = 'eu-west-1'

from ..index import Item


def test_bool_convert():
    item = Item()
    item.item_key = {'key': {'S': 'value'}}
    item.item_value = {
        'string': {'S': 'str'},
        'bool': {'BOOL': 'true'},
        'map': {'M': {
            'string': {'S': 'str'},
            'bool': {'BOOL': 'true'},
        }},
        'list': {'L': [
            {'S': 'str'},
            {'BOOL': 'true'},
        ]},
    }
    out = item.construct_item()
    assert out['string']['S'] == 'str'

    assert isinstance(out['bool']['BOOL'], bool)
    assert out['bool']['BOOL'] is True

    assert isinstance(out['map']['M']['bool']['BOOL'], bool)
    assert out['map']['M']['bool']['BOOL'] is True

    assert isinstance(out['list']['L'][1]['BOOL'], bool)
    assert out['list']['L'][1]['BOOL'] is True
