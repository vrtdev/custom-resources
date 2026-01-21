from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Renotify(LambdaBackedCustomResource):
    """
    Re-trigger the AutoScalingGroup Notification.

    Useful to include with additional "DependsOn" resources.
    """
    props = {
        'AutoScalingGroupName': (str, True),
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "autoscaling:DescribeNotificationConfigurations",
                    "sns:Publish",
                ],
                "Resource": "*",
            }],
        }
