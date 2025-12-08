from .LambdaBackedCustomResource import LambdaBackedCustomResource


class SolutionStackName(LambdaBackedCustomResource):
    props = {
        'Platform': (str, True),  # PHP 7.0
        'Architecture': (str, False),  # Defaults to 64bit
        'AmiStartsWith': (str, False),  # Defaults to '' (everything matches)
        'EbMajorVersion': (int, False),  # Defaults to None (any)
        'EbMinorVersion': (int, False),  # Defaults to None (any)
        'EbPatchVersion': (int, False),  # Defaults to None (any)
        'Serial': (str, False),  # Use this to force an update
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": "elasticbeanstalk:ListAvailableSolutionStacks",
                "Resource": "*",
            }],
        }


class EnvironmentResources(LambdaBackedCustomResource):
    props = {
        'EnvironmentId': (str, True),  # Ref(eb_environment)
        'Serial': (str, False),  # Use this to force an update
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": "elasticbeanstalk:Describe*",
                "Resource": "*",
            }],
        }
