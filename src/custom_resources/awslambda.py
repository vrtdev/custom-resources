from .LambdaBackedCustomResource import LambdaBackedCustomResource


class Version(LambdaBackedCustomResource):
    props = {
        'FunctionName': (str, True),
        'Description': (str, False),
        'CodeSha256': (str, False),
        'Dummy': (str, False),  # Dummy parameter to trigger updates
    }

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "lambda:ListVersionsByFunction",
                    "lambda:PublishVersion",
                    "lambda:DeleteFunction",  # Yes, you need to DeleteFunction("func:version") to delete a version
                ],
                "Resource": "*",
            }],
        }

    @classmethod
    def name(cls):
        """
        :rtype: List[str]
        """
        # Keep legacy non-structured name for backward compatibility
        return ['LambdaVersion']


class LayerVersion(LambdaBackedCustomResource):
    props = {
        'LayerName': (str, True),
        'Content': (dict, True),
        'Description': (str, False),
        'LicenseInfo': (str, False),
        'CompatibleArchitecture': ([str], False),
        'CompatibleRuntimes': ([str], False),
        'DeletionPolicy': (str, False),
    }

    @classmethod
    def _update_lambda_settings(cls, settings):
        # It can take a while before the layer is published
        settings['Timeout'] = 300
        return settings

    @classmethod
    def _lambda_policy(cls):
        return {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "lambda:ListLayers",
                    "lambda:ListLayerVersions",
                    "lambda:PublishLayerVersion",
                    "lambda:DeleteLayerVersion",
                    "s3:GetObject",
                ],
                "Resource": "*",
            }],
        }

    @classmethod
    def name(cls):
        """
        :rtype: List[str]
        """
        # Keep legacy non-structured name for backward compatibility
        return ['LambdaLayerVersion']
