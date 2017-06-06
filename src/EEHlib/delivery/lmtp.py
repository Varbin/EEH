from smtplib import LMTP, SMTPHeloError
from .base import BaseDelivery
from urllib.parse import urlparse

import logging
class Delivery(BaseDelivery):
    def __init__(self, config, logger=logging.getLogger("EEH.Delivery")):
        super().__init__(config)

        logger.info("Delivery method: LMTP / SMTP")
        self.logger = logger

        url = urlparse(config["Url"])
        
        self.username = url.username
        self.__password = url.password or ""

        self.eenforce = config.getboolean("Enforce encryption")

        if url.scheme == "unix":
            self.host = url.path
            if not self.host.startswith("/"):
                raise ValueError("You must specify absulte paths for "
                                "UNIX sockets")
            self.port = None
        elif url.scheme == "tcp":
            self.host = url.hostname
            self.port = url.port or 24
        elif url.scheme == "udp":  # UDP port is officially assigned
            raise ValueError("udp is not supported by"
                            "the underlying smtplib (yet)")
        else:
            raise ValueError("Unknown URL-scheme for LMTP")

    def deliver(self, user, domain, message, from_):
        # We are in a small problem here: "domain" must be ignored.
        # The username is sent directy to the LMTP server!
        
        self.logger.info("Delivering message to: {}[@{}]".format(
            user, domain))

        message = str(message)  # message must be easily convertible

        try:
            connection = LMTP(self.host, self.port)
            self.logger.debug("LMTP connection to {}:{} established.".format(
                self.host, self.port))
        except:
            self.logger.critical("Cannot connect to LMTP server!")
            return False


        a = connection.ehlo()  # actually LHLO (LMTP-HELO)
        if a[0] != 250:
            self.logger.critical("Configured LMTP server neither does "
                                 "accept LHLO!")
            return False
                
        try:
            connection.starttls()  # Try it. If it fails it fails...
        except Exception as e:
            self.logger.warning("LMTP does not STARTTLS. {}: {}".format(
                e.__class__, " ".join(e.args)))
            if self.eenforce:
                self.logger.critical("Configured LMTP server does not "
                                     "STARTTLS but this is enforced by "
                                     "configuration!")
                return False
        else:
            a = connection.ehlo()
            if a[0] != 250:
                self.logger.critical("Configured LMTP server neither does "
                                 "accept LHLO!")
                return False
                

        if self.username:
            try:
                connection.login(self.username, self.__password)
            except Exception as e:
                # LMTP does usually not support authentication!
                self.logger.critical(("Cannot log in on LMTP server. "
                                      "{}: {}").format(
                                        e.__class__, " ".join(e.args)))
                return False

        try:
            connection.sendmail(from_, [user], message)
        except Exception as e:
            # This must be a great LMTP / SMTP server ... or our failure :)
            self.logger.critical(("Cannot send mail. "
                                "{}: {}").format(
                                    e.__class__, "{} {}".format(*e.args)))
            return False
        else:
            self.logger.info("Delivery to {}[@{}] successful".format(
                user, domain))
            return True  # Finally :D
