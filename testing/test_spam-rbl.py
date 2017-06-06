import dns.exception
import dns.resolver

from EEHlib.spam import RBL

class FakeResult:
    def __init__(self, records):
        self.strings = records
        self.exchange = self

    def __iter__(self):
        return map(lambda c: FakeResult([c]), self.strings)

    def __getitem__(self, *args):
        return self

    def to_text(self, x=None):
        return self.strings[0].decode()

class FakeResolver:
    domains = {}
    @classmethod
    def add_domain(cls, domain, record, contents):
        d = cls.domains.get(domain, {})
        d[record] = FakeResult([content.encode() for content in contents])
        cls.domains[domain] = d

    def query(self, host, record):
        dd = FakeResolver.domains.get(host, {})
        if not dd:
            raise dns.resolver.NXDOMAIN
        if dd.get("TIMEOUT") is not None:
            raise dns.exception.Timeout
        r = dd.get(record)
        if not r:
            raise dns.rdatatype.UnknownRdatatype
        else:
            return r

    @classmethod
    def gethostbyname(cls, host):
        if not cls.domains.get(host):
            raise Exception("Unknown host")
        if not cls.domains.get(host).get('A'):
            raise Exception("No A record")
        else:
            return cls.domains.get(host).get('A').to_text()

    @classmethod
    def gethostbyaddress(cls, address):
        ip = address
        if not cls.domains.get(host):
            raise OSError
        if not cls.domains.get(host)('PTR'):
            raise OSError
        else:
            return cls.domains.get(host)('PTR').to_text(), [], ip

FakeResolver.add_domain("1.0.0.127.dnsbl.example", "A", ["127.0.0.1"])
FakeResolver.add_domain("2.0.0.127.dnsbl.example", "A", ["127.0.0.1"])
FakeResolver.add_domain("2.0.0.127.dnsbl.example", "TXT", ["REASON"])
FakeResolver.add_domain("3.0.0.127.dnsbl.example", "TIMEOUT", [])
RBL.dns.resolver.Resolver = FakeResolver


def test_dummy():
    assert isinstance(RBL.RBL([]), RBL.RBLdummy)

def test_checker():
    assert isinstance(RBL.RBL(["dnsbl.example"]), RBL.RBLchecker)

def test_clean():
    rbl = RBL.RBL(["dnsbl.example"])
    assert isinstance(rbl, RBL.RBLchecker)
    assert rbl.validate("127.0.0.4") is None

def test_blocked():
    rbl = RBL.RBL(["dnsbl.example"])
    assert isinstance(rbl, RBL.RBLchecker)
    r = rbl.validate("127.0.0.2")
    assert r.startswith("554") and "REASON" in r
    r = rbl.validate("127.0.0.1")
    assert r.startswith("554") and "Unknown reason." in r

def test_timeout():
    rbl = RBL.RBL(["dnsbl.example"])
    assert rbl.validate("127.0.0.3") is None

if __name__ == "__main__":
    import __main__
    for i in dir(__main__):
        if i.startswith("test_"):
            print("---", i)
            eval(i).__call__()
