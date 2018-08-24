from .acm import DnsValidatedCertificate


# Backward compatibility
class AcmDnsValidatedCertificate(DnsValidatedCertificate):
    _deprecated = 1535105258
    _deprecated_message = 'Use custom_resources.acm.DnsValidatedCertificate() instead'
