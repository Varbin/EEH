import dns.resolver
import dns.reversename
from dns.exception import Timeout
import logging


def RBL(dnsbls=(), logger=logging.getLogger("EEH.RBL")):
    """Constructor to choose between a real and a dummy RBL class.
    This is not a class!"""
    if not dnsbls:
        logger.info("RBL not configured!")
        return RBLdummy(dnsbls, logger)
    else:
        return RBLchecker(dnsbls, logger)


class RBLdummy:
    def __init__(self, dnsbls, logger=logging.getLogger("EEH.RBL")):
        self.logger = logger
        self.dnsbls = dnsbls

    def validate(self, peer):
        self.logger.debug("NOT checking {}: not configured".format(peer))


class RBLchecker(RBLdummy):
    # code from
    #  http://www.iodigitalsec.com/dns-black-list-rbl-checking-in-python/

    def validate(self, peer):
        reverse = str(dns.reversename.from_address(peer).split(3)[0])

        for bl in self.dnsbls:
            try:
                resolver = dns.resolver.Resolver()
                query = ".".join([reverse, bl])
                self.logger.debug("Checking {} on {}".format(
                    peer, bl))
                try:
                    resolver.query(query, "A")
                except Timeout:
                    self.logger.warning("Timeout on {}".format(peer))
                    continue
                try:
                    answer = resolver.query(query, "TXT"
                                            )[0].strings[0].decode()
                except:
                    answer = "Unknown reason."
                self.logger.info("Client host [{}] blocked using {}".format(
                    peer, bl))
                return (
                    "554 5.7.1 Service unavailable; "
                    "Client host [{}] blocked using {}: {}"
                    ).format(peer, bl, answer)
            except dns.resolver.NXDOMAIN:
                pass
