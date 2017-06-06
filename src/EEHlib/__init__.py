#!/usr/bin/env python3

from __future__ import print_function

from email.utils import formatdate

import dns.resolver
import base64
# import ipaddress
import gc
import logging
import mailbox
import os
import smtpd
import socket
import sys
import time
import smtplib
import asynchat
import email

from .spam.RBL import RBL
from .channel import StartTLSFutureChannel as StartTLSChannel
from .channel import bootstrap_futures
from .version import __version__


#from .corefutures import bootstrap as bootstrap_futures
#from .corefutures import CoreFuture

try:
    import ssl
except ImportError:
    class ssl:
        SSLSocket = NotImplemented
        SSLWantReadError = NotImplemented
        SSLWantWriteError = NotImplemented

ALLOW_ALL_USERS = "ALL"
ALLOW_FILE_USERS = "FILE"

CONFIG = "EEH.conf"
DEFAULT_DOMAINS = ("localhost", "localhost.localdomain")


bootstrap_futures()  # Threads, processor count * 5


def rfc1123():
    "Returns the time now formatted as stated in RFC 1123."
    return formatdate(time.time(), 0, 1)


class EEHd(smtpd.SMTPServer):
    """
    Main class of EEH. It stores all settings for an EEH instance.
    It is a subclass of smtpd.SMTPServer which is a subclass
    of asyncore.dispatcher so it integrates in the (outdated) asyncore
    framework.

    The process_message handles actuall message delivery.
    """
    channel_class = StartTLSChannel

    def __init__(self, *args, user_driver=None, delivery=None,
                 domains=DEFAULT_DOMAINS,
                 check_domains=True, rbls=(), logger=logging.getLogger("EEH.EEHd"),
                 extra_gc=True, ssl_ctx=None, banner="ESMTP EEH ready.", **kwargs):
        super().__init__(*args, **kwargs)

        # Monkeypatch smtpd for custom version string
        smtpd.__version__ = banner

        mid = None
        self.ctx = ssl_ctx

        self.user_driver = user_driver
        self.delivery = delivery

        self.domains = domains
        self.check_domains = check_domains

        self.rbl_checker = RBL(rbls)

        self.logger = logger
        self.gc = extra_gc

    def _return(self, mid, data):
        self.log_error(mid, data)
        if self.gc:
            print("GC:", gc.collect())
        return data

    def log_info(self, mid, data):
        self.logger.info("{}: {}".format(mid, data))

    def log_warning(self, mid, data):
        self.logger.warning("{}: {}".format(mid, data))

    def log_error(self, mid, data):
        self.logger.error("{}: {}".format(mid, data))

    def process_message(self, peer, sender, recipients, data,
                        mail_options=(), rcpt_options=(),
                        greeting="", cipher="", **kwargs):
        """
        The message processing function.

        Arguments:

         - peer: tuple(remote_ip, port)
         - sender: sender's mail address
         - recipients: list(recipient_1, recipient_2, ..., recipient_n)
         - data: The Mail
         - mail_options: list(mail_parameter_1.upper(), ...,
                              mail_parameter_n.upper())
         - rcpt_options: same as mail_options but for the RCPT command
         - greeting (optional): HELO/EHLO greeting
         - cipher (optional): SSL/TLS cipher suite
        """

        mid = base64.b32encode(os.urandom(10)).decode()
        self.log_info(mid, "Message To {} From <{}> ({})".format(
            str(recipients), sender, peer[0]))

        recieved_header = (
            "from {greeting} ({reverse} [{peer}])\r\n"
            "\tby {me} (Easy Email Host) with ESMTP{s} id {mid}\r\n"
            "\tfor {recipients}; {time}").format(greeting=greeting,
                                                 reverse=socket.getfqdn(peer[0]), peer=peer[0],
                                                 s=("s ({})".format(cipher)) if cipher is not None else "",
                                                 me=socket.getfqdn(), mid=mid,
                                                 recipients=", ".join(map("<{}>".format, recipients)),
                                                 time=rfc1123())

        rbl_result = self.rbl_checker.validate(peer[0])
        if rbl_result:
            return self._return(mid, rbl_result)

        internal_users = {}
        external_users = []

        for recipient in recipients:
            # It's safe to fail here because there is a general failure.

            if recipient.count("@") != 1:
                return self._return(mid, "501 5.1.3 Bad email address")

            if "\\" in recipient or " " in recipient:  # / is actually allowed
                return self._return(mid, "501 5.1.3 Bad email address")

            user, _unused, host = recipient.lower().partition("@")

            if not user or not host:
                return self._return(mid, "501 5.1.3 Bad email address")

            if host not in self.domains and self.check_domains:
                return self._return(mid, (
                    '551 5.7.1 User "{}" not local, he/she is at "{}"'
                    ' - Relay access denied').format(user, host))

            results = self.user_driver.resolve_user(user)

            for result in results:
                user, _unused, nhost = result.partition("@")
                if (nhost not in self.domains and
                        self.check_domains) and nhost:
                    external_users.append(result)
                else:
                    internal_users[result] = nhost or host

        if not (internal_users or external_users):
            # Fail (and leak) on invalid users)
            return self._return(mid, '550 5.1.1 Bad destination mailbox address')

        message = email.message_from_bytes(data)
        message["Received"] = recieved_header

        m = str(message)

        success_count = 0
        failure_count = 0

        # DESIGN DECISION: Hard fail on partial failure of delivery.
        #  Why that?
        #   a) Privacy: Does not leak email address.
        #       NOTE: It does leak when there is not even one valid receiver!
        #   b) Delivers where possible. Highest risk is double delivery.
        #       Without a mail queue it is impossible to solve this.

        for user in internal_users.keys():
            domain = internal_users[user]
            self.log_info(mid, "Delivering to: {}[@{}]".format(user, domain))

            if self.user_driver.is_accepted_user(user):
                success = self.delivery.deliver(user, domain, message, sender)
            else:
                failure_count += 1
                continue

            if not success:
                # failures["@".join((user, domain))] = True
                failure_count += 1
            else:
                success_count += 1

        for email_address in external_users:
            self.log_info(mid, "Delivering to: {}".format(email_address))
            user, _, host = email_address.lower().partition("@")
            exchanges = {}
            try:
                for x in dns.resolver.query(host, 'MX'):
                    if ("your-dns-needs-immediate-attention."
                            in x.exchange.to_text(True)):
                        self.log_info(mid,
                                      "Invalid MX-record for domain \"{}\"".format(
                                          host))
                        continue
                    if x.preference not in exchanges:
                        exchanges[x.preference] = []
                    exchanges[x.preference].append(x.exchange.to_text(True))
            except dns.resolver.NoAnswer:
                self.log_info(mid,
                              "Invalid MX-record for domain \"{}\"".format(
                                  host))

            # If there's no MX entry: Do normal resolving
            if not exchanges:
                self.log_warning(mid,
                                 "No valid MX-record for domain \"{}\"".format(host))
                # socket.gethostbyname for simple resolving!
                try:
                    exchanges[0] = [socket.gethostbyname(host)]
                except OSError:  # Since Py 3.3 socket errors are a subclass of OSError
                    self.log_error(mid,
                                   "Domain \"{}\" could not be resolved".format(host))

            if not exchanges:  # After failure resolving A
                failure_count += 1
                continue  # 

            _break = False
            for priority in sorted(exchanges.keys()):
                for exchange in exchanges[priority]:
                    try:
                        try:
                            # Try SMTPS first:
                            #  - Mailservers with no support for STARTTLS
                            #     (like EEH)
                            #  - Rogue providers 
                            connection = smtplib.SMTP_SSL(exchange)
                            smtps = True
                        except:
                            connection = smtplib.SMTP(exchange)
                            smtps = False
                        connection.ehlo_or_helo_if_needed()
                        if not smtps:
                            try:
                                connection.starttls()
                                # Reinitia
                                connection.ehlo_or_helo_if_needed()
                            except Exception as e:
                                self.log_info(mid,
                                              (
                                                  "No TLS/SSL for domain \"{}\". Error is:"
                                                  "{} {}").format(exchange, e.__class__,
                                                                  " ".join(e.args)))
                        connection.sendmail(sender, [email_address],
                                            str(message))
                    except Exception as e:
                        self.log_warning(mid,
                                         (
                                             "Could not deliver to \"{}\". Error is:"
                                             "{} {}").format(exchange, e.__class__,
                                                             " ".join(e.args)))
                    else:  # Successful delivery
                        self.log_info(mid, "Delivery to {} successful".format(
                            email_address))
                        _break = True
                        break
                if _break:
                    break
            else:
                self.log_error(mid, "Could not deliver external mail!")
                failure_count += 1

        if failure_count:
            return self._return(mid,
                                ("550 5.5.0 Could not deliver to some users. "
                                 "{} delivery/deliveries successful, "
                                 "{} delivery/deliveries failed.").format(success_count,
                                                                          failure_count, ))
