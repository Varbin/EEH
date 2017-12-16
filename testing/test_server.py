import os
from threading import Thread
from socket import getfqdn
from functools import partial
import pytest
import time

from _smtp_wait import SMTP
Connection = partial(SMTP, "localhost", 10025)

PATH = os.path.abspath(os.path.dirname(__file__))

from EEH import main

def server():
    import os
    os.chdir(PATH)
    main.callback('test.conf', 'normal')

def background_server():
    p = Thread(
        target=server, name="EEH-main", daemon=True)
    p.start()
    return p

b = background_server()

def test_helo():
    with Connection() as s:
        assert s.docmd('HELO') == (501, b'5.5.4 Syntax: HELO hostname')
        assert s.docmd('HELO', 'localhost') == (250, getfqdn().encode())
        assert s.docmd('EHLO') == (501, b'5.5.4 Syntax: EHLO hostname')
        a,b = s.docmd('EHLO', 'localhost')
        assert a == 250 and b.startswith(getfqdn().encode())
        assert b"STARTTLS" in b
    
def test_noop():
    with Connection() as s:
        assert s.docmd('NOOP') == (250, b'2.0.0 OK')

def test_rset():
    with Connection() as s:
        assert s.docmd('RSET') == (250, b'2.0.0 OK')
        assert s.docmd('RSET', 'error') == (501, b'5.5.4 Syntax: RSET')

def test_vrfy():
    with Connection() as s:
        assert s.docmd('VRFY') == (501, b'5.5.4 Syntax: VRFY <address>')
        assert s.docmd('VRFY', 'test') == (
            252, (
                b'2.0.0 Cannot VRFY user, '
                b'but will accept message and attempt delivery'))

def test_expn():
    with Connection() as s:
        assert s.docmd('EXPN') == (502, b'5.5.0 EXPN not implemented')

def test_starttls():
    with Connection() as s:
        assert s.docmd('STARTTLS', 'error') == (501, b'5.5.4 Syntax: STARTTLS')
        assert s.starttls() == (220, b'2.0.0 Ready to start TLS')
        assert s.docmd('STARTTLS') == (503, b'5.5.1 Bad sequence of commands.')

def test_data():
    with Connection() as s:
        assert s.docmd('DATA', 'error') == (501, b'5.5.4 Syntax: DATA')
        assert s.docmd('DATA') == (503, b'5.5.0 Error: send HELO first')
        s.helo()
        assert s.docmd('DATA') == (503, b'5.5.0 Error: need RCPT command')
        s.mail('test@localhost')
        s.rcpt('user1@localhost')
        assert s.data('TEST') == (250, b'2.0.0 OK')

def test_data_unknown_recipient():
    with Connection() as s:
        s.helo()
        s.mail('test@localhost')
        s.rcpt('user2@localhost')
        a,b = s.data('test')
        assert a == 550 and b.startswith(b'5.5.0')

def test_rset_working():
    with Connection() as s:
        s.helo()
        s.mail('test@localhost')
        s.rcpt('user1@localhost')
        s.rset()
        # s.data would raise an exception
        assert s.docmd('DATA') == (503, b'5.5.0 Error: need RCPT command')

def test_help():
    with Connection() as s:
        a,b = s.docmd('HELP')
        assert a == 250
        assert b.startswith(b"Supported commands: ")  
        a,b = s.docmd('HELP', 'UNKNOWN')
        assert a == 501
        assert b.startswith(b"Supported commands: ")

        assert s.docmd('HELP', 'MAIL') == (250, b'Syntax: MAIL FROM: <address>')
        assert b'HELP' in s.ehlo()[1]
        assert s.docmd('HELP', 'MAIL') == (250,
               b'Syntax: MAIL FROM: <address> [SP <mail-parameters]')

def test_quit():
    with Connection() as s:
        assert s.quit() == (221, b'2.0.0 Bye. Have a nice day!')

def test_error():
    with Connection() as s:
        assert s.docmd('') == (501, b'5.2.2 Error: Bad syntax.')
        assert s.docmd('ERROR'*1000) == (
            500, b'5.5.2 Error: line too long.')
        assert s.docmd('INVALID') == (
            500, b'5.5.1 Error: command "INVALID" not recognized')

if __name__ == "__main__":
    error = True
    while error:
        try:
            s = Connection()
        except ConnectionRefusedError:
            pass
        else:
            error = False

    i = None
    for i in globals().keys():
        if i.startswith("test_"):
            print('---', i)
            eval(i).__call__()

