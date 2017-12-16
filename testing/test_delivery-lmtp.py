import pytest
import mailbox
import asyncore
import time

from multiprocessing import Process
from functools import partial
from smtpd import SMTPChannel, SMTPServer

from _smtp_wait import SMTP
Connection = partial(SMTP, "localhost", 10024)  # wait for server

def wait_for_server():
    with Connection() as s:
        s.quit()

class LMTPChannel(SMTPChannel):
  # LMTP "LHLO" command is routed to the SMTP/ESMTP command
  def smtp_LHLO(self, arg):
    self.smtp_HELO(arg)

class LMTPServer(SMTPServer):
  def __init__(self, localaddr, remoteaddr, fail, channel):
    SMTPServer.__init__(self, localaddr, remoteaddr)
    self.fail = fail
    self.channel = channel

  def process_message(self, *args, **kwargs):
    return "500 Fail" if self.fail else "250 Ok"

  def handle_accept(self):
    conn, addr = self.accept()
    channel = self.channel(self, conn, addr)


def server_and_loop(*args, **kwargs):
    server = LMTPServer(*args, **kwargs)
    asyncore.loop()

def background_server(fail, channel=LMTPChannel):
    p = Process(
        target=server_and_loop, args=(
            ('localhost', 10024), None, fail, channel))
    p.start()
    return p


from EEHlib.delivery.lmtp import Delivery

class C(dict):
    def getboolean(self, attr, fallback=False):
        return bool(self.get(attr)) or fallback

CONFIG_LOCAL = C({
    "Url":"tcp://localhost:10024"})

def test_syntax():
    d1 = Delivery(C({"Url":"tcp://user@localhost"}))
    assert d1.host == "localhost"
    assert d1.port == 24
    assert d1.username == "user"

    with pytest.raises(ValueError):
        d2 = Delivery(C({"Url":"unix://test"}))

    d3 = Delivery(C({"Url":"unix:///test"}))
    assert d3.host == "/test"

    with pytest.raises(ValueError):
        d4 = Delivery(C({"Url":"udp://user@localhost"}))

    with pytest.raises(ValueError):
        d5 = Delivery(C({"Url":"http://user@localhost"}))
    

def test_connection():
    d = Delivery(CONFIG_LOCAL)
    assert not d.deliver("test", "invalid.fqdn", "Test", "test@example.org")
    
    b = background_server(False)
    
    wait_for_server()

    try:
        assert d.deliver("test", "invalid.fqdn", "Test", "test@example.org")
    finally:
        b.terminate()
    
    b = background_server(True)
    
    wait_for_server()

    try:
        assert not d.deliver(
            "test", "invalid.fqdn", "Test", "test@example.org")
    finally:
        b.terminate()

def test_eenforce():
    c = C(CONFIG_LOCAL.copy())
    c["Enforce encryption"] = True
    d = Delivery(c)
    b = background_server(False)
    wait_for_server()
    try:
        assert not d.deliver(
            "test", "invalid.fqdn", "Test", "test@example.org")
    finally:
        b.terminate()

def test_failedauth():
    c = C({
        "Url":"tcp://test@localhost:10024"})
    d = Delivery(c)
    b = background_server(False)
    wait_for_server()
    try:
        assert not d.deliver(
            "test", "invalid.fqdn", "Test", "test@example.org")
    finally:
        b.terminate()

def test_smtp():
    d = Delivery(CONFIG_LOCAL)
    b = background_server(False, SMTPChannel)
    wait_for_server()
    try:
        assert not d.deliver(
            "test", "invalid.fqdn", "Test", "test@example.org")
    finally:
        b.terminate()

if __name__ == "__main__":
    import __main__
    for i in dir(__main__):
        if i.startswith("test_"):
            print("---", i)
            eval(i).__call__()
