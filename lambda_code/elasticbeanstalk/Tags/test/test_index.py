from ..index import Tags


def test_tags_dict_to_list():
    tags_to_add = Tags.tags_to_update({'LabelOwner': 'kenisro', 'LabelProject': 'video-monitoring-ui'})

    assert tags_to_add == [{'Key': 'LabelOwner', 'Value': 'kenisro'},
                           {'Key': 'LabelProject', 'Value': 'video-monitoring-ui'}]


def test_tags_dict_to_list_empty():
    tags_to_add = Tags.tags_to_update({})

    assert tags_to_add == []
