import time

from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Tags(LambdaBackedCustomResource):
    """
    Custom Resource to extract tags from the CloudFormation Stack, and
    expose them via GetAtt() to other resources that don't automatically
    inherit the tags from the stack (e.g. custom resources).

    Caveat: Some resources fail when no tags are present. It is advisable to
    always configure a tag to be added (via Set={"foo":"bar"}) to avoid this
    case.
    """
    props = {
        'Omit': ([str], False),  # Keys to remove from list
        'Set': (dict, False),  # Keys to set/override/add, with the new values
        'Dummy': (str, False),  # Dummy parameter to trigger updates
    }

    def __init__(self, *args, **kwargs):
        if 'Dummy' not in kwargs:
            kwargs['Dummy'] = str(time.time())  # Force refresh as much as possible

        super(Tags, self).__init__(*args, **kwargs)

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "cloudformation:DescribeStacks",
                ],
                "Resource": "*",
            }],
        }
