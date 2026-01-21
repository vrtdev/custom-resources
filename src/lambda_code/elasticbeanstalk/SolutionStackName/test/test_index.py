from ..index import SolutionStackName


def test_solution_stack_name():
    stack_info = SolutionStackName.split_solution_stack_name(
        '64bit Amazon Linux 2018.03 v2.7.4 running Python 3.6'
    )
    assert stack_info == {
        'arch': '64bit',
        'ami': 'Amazon Linux 2018.03',
        'major': 2,
        'minor': 7,
        'patch': 4,
        'platform': 'Python 3.6',
    }
