from .ec2 import FindAmi


# Backward compatibility
class Ec2FindAmi(FindAmi):
    _deprecated = 1535105258
    _deprecated_message = 'Use custom_resources.ec2.FindAmi() instead'
