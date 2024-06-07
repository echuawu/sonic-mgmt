""" Class to describe info about certificate in test environment """


class CertInfo:
    def __init__(self, info, key, cert, p12_bundle, dn, ip, cacert):
        self.info: str = info
        self.key: str = key
        self.cert: str = cert
        self.p12_bundle: str = p12_bundle
        self.dn: str = dn
        self.ip: str = ip
        self.cacert: str = cacert

    @property
    def key_filename(self) -> str:
        return None if not self.key else self.key.split('/')[-1]

    @property
    def cert_filename(self) -> str:
        return None if not self.cert else self.cert.split('/')[-1]

    @property
    def bundle_filename(self) -> str:
        return None if not self.p12_bundle else self.p12_bundle.split('/')[-1]

    @property
    def cacert_filename(self) -> str:
        return None if not self.cacert else self.cacert.split('/')[-1]
