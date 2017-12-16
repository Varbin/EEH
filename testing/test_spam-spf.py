class FakeResult:
    def __init__(self, records):
        self.strings = records
        self.exchange = self

    def __iter__(self):
        return map(lambda c: FakeResult([c]), self.strings)

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

import dns.resolver
import socket

socket._gethostbyname = socket.gethostbyname
dns.resolver._Resolver = dns.resolver.Resolver

FakeResolver.add_domain("127.0.0.0", "A", ["127.0.0.0"])
FakeResolver.add_domain("127.0.0.1", "A", ["127.0.0.1"])
FakeResolver.add_domain("127.0.0.2", "A", ["127.0.0.2"])
FakeResolver.add_domain("33.1.33.2", "A", ["33.1.33.2"])

FakeResolver.add_domain("test1.example", "TXT", ["v=spf +all"])
FakeResolver.add_domain("test2.example", "TXT", ["v=spf -all"])
FakeResolver.add_domain("test3.example", "TXT", ["v=spf ~all"])
FakeResolver.add_domain("test4.example", "TXT", ["v=spf ?all"])
FakeResolver.add_domain("test5.example", "TXT", ["v=spf all"])
FakeResolver.add_domain("test6.example", "TXT", ["v=spf invalid"])
FakeResolver.add_domain("test7.example", "TXT", ["Hello World!"])
FakeResolver.add_domain("test8.example", "TXT", ["v=spf exp=message"])

FakeResolver.add_domain("test1_a.example", "A", ["127.0.0.1"])
FakeResolver.add_domain("test1_a.example", "TXT",
                        ["v=spf -ip4:127.0.0.2 A:test1_a.example -all"])
FakeResolver.add_domain("test1_a2.example", "TXT",
                        ["v=spf A:127.0.0.1/8 -all"])
FakeResolver.add_domain("test1_a3.example", "A", ["127.0.0.1"])
FakeResolver.add_domain("test1_a3.example", "TXT",
                        ["v=spf A -all"])

FakeResolver.add_domain("test1_b.example", "MX", ["127.0.0.1"])
FakeResolver.add_domain("test1_b2.example", "MX", ["127.0.0.0"])
FakeResolver.add_domain("test1_b.example", "TXT",
                        [("v=spf "
                          "MX -MX:test1_b2.example/8")])

FakeResolver.add_domain("test1_c.example", "TXT", [
    "v=spf exp=message include:test1.example  -all"])

FakeResolver.add_domain("test1_d.example", "TXT",[
    "v=spf exists:127.0.0.1 -all"])
FakeResolver.add_domain("test1_d.example", "A", ["127.0.0.1"])
FakeResolver.add_domain("test1_d2.example", "TXT",[
    "v=spf exists -all"])

FakeResolver.add_domain("test1_e.example", "TXT",[
    "v=spf redirect:test1.example -all"])

FakeResolver.add_domain("127.0.0.1:", "PTR",[
    "127.0.0.1"])
FakeResolver.add_domain("test1_f2.example", "PTR",[
    "127.0.0.2"])
FakeResolver.add_domain("test1_f.example", "TXT",[
    "v=spf -ptr:test1_f.example"])


from EEHlib.spam import SPF
SPF.socket.gethostbyname = FakeResolver.gethostbyname
SPF.Resolver = FakeResolver


def result(code):
    return (code,) + SPF.statusmap[code]

for i in (
    "PASS", "FAIL", "SOFTFAIL", "NEUTRAL", "PERMERROR", "TEMPERROR", "NONE"):

    exec("SPF_{0} = result(SPF.{0})".format(i))

#def pre():
#    global socket, dns


#def end():
#    global socket, dns
#    socket.gethostbyname = socket._gethostbyname
#    dns.resolver.Resolver = dns.resolver._Resolver

def test_all():
    assert SPF.spf("test1.example", "127.0.0.1") == SPF_PASS
    assert SPF.spf("test2.example", "127.0.0.1") == SPF_FAIL
    assert SPF.spf("test3.example", "127.0.0.1") == SPF_SOFTFAIL
    assert SPF.spf("test4.example", "127.0.0.1") == SPF_NEUTRAL
    assert SPF.spf("test5.example", "127.0.0.1") == SPF_PASS
    #assert SPF.spf("test6.example", "127.0.0.1") == SPF_PERMERROR
    assert SPF.spf("test7.example", "127.0.0.1") == SPF_NEUTRAL
    assert SPF.spf("test8.example", "127.0.0.1") == SPF_NONE


def test_a_ip():
    assert SPF.spf("test1_a.example", "127.0.0.1") == SPF_PASS
    assert SPF.spf("test1_a.example", "127.0.0.2") == SPF_FAIL
    assert SPF.spf("test1_a.example", "33.1.33.2") == SPF_FAIL
    assert SPF.spf("test1_a2.example", "127.0.0.2") == SPF_PASS
    assert SPF.spf("test1_a2.example", "33.1.33.2") == SPF_FAIL
    assert SPF.spf("test1_a3.example", "127.0.0.1") == SPF_PASS
    assert SPF.spf("test1_a3.example", "127.0.0.2") == SPF_FAIL

    
def test_a_mx():
    assert SPF.spf("test1_b.example", "127.0.0.1") == SPF_PASS
    assert SPF.spf("test1_b.example", "127.0.0.2") == SPF_FAIL

def test_include():
    assert SPF.spf("test1_c.example", "127.0.0.1") == SPF_PASS

def test_exists():
    assert SPF.spf("test1_d.example", "127.0.0.1") == SPF_PASS
    assert SPF.spf("test1_d2.example", "127.0.0.1") == SPF_PASS

def test_redirect():
    assert SPF.spf("test1_e.example", "127.0.0.1") == SPF_PASS


if __name__ == "__main__":
    import __main__
    for i in dir(__main__):
        if i.startswith("test_"):
            print("---", i)
            eval(i).__call__()
