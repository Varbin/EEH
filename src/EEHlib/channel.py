import asynchat
import smtpd
from concurrent import futures
#from tls import TLSHandshaker
from .tls import TLSHandshaker

try:
    from multiprocessing import cpu_count
except ImportError:
    # some platforms don't have multiprocessing
    def cpu_count():
        return 1

import sys

try:
    import ssl
except ImportError:
    class ssl:
        SSLSocket = NotImplemented
        SSLWantReadError = NotImplemented
        SSLWantWriteError = NotImplemented


executor = None

def bootstrap_futures(pool=futures.ThreadPoolExecutor, max_workers=None):
    global executor

    if executor is not None:
        executor.shutdown()

    if max_workers is None:
        max_workers = cpu_count() * 5

    executor=pool(max_workers=max_workers)


SMTP_HELP = {
    'EHLO' : '250 Syntax: EHLO hostname',
    'HELO' : '250 Syntax: HELO hostname',
    'MAIL' : '250 Syntax: MAIL FROM: <address>',
    'RCPT' : '250 Syntax: RCPT FROM: <address>',
    'MAIL_e' : '250 Syntax: MAIL FROM: <address> [SP <mail-parameters]',
    'RCPT_e' : '250 Syntax: RCPT FROM: <address> [SP <mail-parameters]',
    'DATA' : '250 Syntax: DATA',
    'NOOP' : '250 Syntax: NOOP [SP String]',
    'QUIT' : '250 Syntax: QUIT',
    'VRFY' : '250 VRFY <address>',
    'HELP' : '250 HELP [SP String]',
}


class ExtensionChannel(smtpd.SMTPChannel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmd_help = SMTP_HELP.copy()
        self.cmd_list = sorted([
            e for e in self.cmd_help.keys() if not e.endswith('_e')])

        self.extensions = ['ENHANCEDSTATUSCODES']
        if self.data_size_limit:
            self.extensions.append('SIZE %s' % self.data_size_limit)
            self.command_size_limits['MAIL'] += 26

        if not self._decode_data:
            self.extensions.append('8BITMIME')

        if self.enable_SMTPUTF8:
            self.extensions.append('SMTPUTF8')
            self.command_size_limits['MAIL'] += 10

        self.extensions.append('HELP')

    __init__.__doc__ = smtpd.SMTPChannel.__init__.__doc__  # 16*_


    def smtp_HELO(self, arg):
        if not arg:
            self.push('501 5.5.4 Syntax: HELO hostname')
            return

        self._set_rset_state()
        self.seen_greeting = arg
        self.push('250 %s' % self.fqdn)

    def smtp_EHLO(self, arg):
        if not arg:
            self.push('501 5.5.4 Syntax: EHLO hostname')
            return

        self._set_rset_state()
        self.seen_greeting = arg
        self.extended_smtp = True
        self.push('250-%s' % self.fqdn)

        extensions = sorted(self.extensions)

        for extension in extensions[:-1]:
            self.push('250-%s' % extension)

        self.push('250 %s' % extensions[-1])


    def smtp_NOOP(self, arg):
        self.push('250 2.0.0 OK')

    def smtp_QUIT(self, arg):
        self.push('221 2.0.0 Bye. Have a nice day!')
        self.close_when_done()

    def smtp_RSET(self, arg):
        if arg:
            self.push('501 5.5.4 Syntax: RSET')
            return
        self._set_rset_state()
        self.push('250 2.0.0 OK')

    def smtp_DATA(self, arg):
        if arg:
            self.push('501 5.5.4 Syntax: DATA')
            return
        if not self.seen_greeting:
            self.push('503 5.5.0 Error: send HELO first');
            return
        if not self.rcpttos:
            self.push('503 5.5.0 Error: need RCPT command')
            return
        self.smtp_state = self.DATA
        self.set_terminator(b'\r\n.\r\n')
        self.push('354 End data with <CR><LF>.<CR><LF>')

    def smtp_VRFY(self, arg):
        if not arg:
            self.push('501 5.5.4 Syntax: VRFY <address>')
            return
        self.push('252 2.0.0 Cannot VRFY user, '
                  'but will accept message and attempt delivery')

    # Command that have not been implemented
    def smtp_EXPN(self, arg):
        self.push('502 5.5.0 EXPN not implemented')

    def smtp_HELP(self, arg):
        if arg:
            lc_arg = arg.upper()

            command_help = self.cmd_help.get(
                lc_arg, '501 Supported commands: {}'.format(
                    ' '.join(self.cmd_list)))

            if self.extended_smtp:
                command_help = self.cmd_help.get(
                    lc_arg+'_e', command_help)

            self.push(command_help)
        else:
            self.push('250 Supported commands: {}'.format(
                    ' '.join(self.cmd_list)))


class BackgroundChannel(ExtensionChannel):
    in_background = False

    def writable(self):
        # Disable this channel while in handshake
        if not self.in_background:
            return super().writable()
        else:
            return False

    def readable(self):
        # Disable this channel while in handshake
        if not self.in_background:
            return super().readable()
        else:
            return False


class StartTLSChannel(BackgroundChannel):
    in_background = False
    cipher = None

    def __init__(self, *args, **kwargs):
        ExtensionChannel.__init__(self, *args, **kwargs)
        self.cmd_help["STARTTLS"] = '250 Syntax: STARTTLS'
        self.cmd_list.append("STARTTLS")
        self.cmd_list = sorted(self.cmd_list)

        if self.smtp_server.ctx is not None:
            self.extensions.append("STARTTLS")
        

    def smtp_STARTTLS(self, arg):
        if arg:
            self.push('501 5.5.4 Syntax: STARTTLS')

        elif self.smtp_server.ctx is not None and not isinstance(
                self.conn, ssl.SSLSocket):
            self.push('220 2.0.0 Ready to start TLS')

            self.extensions.pop(self.extensions.index('STARTTLS'))

            self.in_handshake = True

            self.conn = self.smtp_server.ctx.wrap_socket(
                self.conn, server_side=True,
                do_handshake_on_connect=False)

            channel = TLSHandshaker(self.conn, self)

            # Reset connection data
            self._set_rset_state()
            self.command_size_limits.clear()
        elif isinstance(self.conn, ssl.SSLSocket):
            self.push("503 5.5.1 Bad sequence of commands.")

        else:
            self.push(
                '454 4.7.0 STARTTLS not available due to temporary reason.')

    def handle_error(self):
        error = sys.exc_info()[1]
        if isinstance(error, (ssl.SSLWantReadError, ssl.SSLWantWriteError)):
            pass  # Just pass, just ignore the (not-)error
        else:
            super().handle_error()

    def replace_connection(self, conn):
        self.conn = conn
        self.in_background = False
        self.cipher = self.conn.cipher()
        asynchat.async_chat.__init__(self, self.conn)  # Reinitialize


class FutureChannel(BackgroundChannel):

    # Implementation of base class abstract method
    def found_terminator(self):
        line = self._emptystring.join(self.received_lines)
        # - print('Data:', repr(line), file=smtpd.DEBUGSTREAM)
        self.received_lines = []
        if self.smtp_state == self.COMMAND:
            sz, self.num_bytes = self.num_bytes, 0
            if not line:
                self.push('501 5.2.2 Error: Bad syntax.')
                return
            if not self._decode_data:
                line = str(line, 'utf-8')
            i = line.find(' ')
            if i < 0:
                command = line.upper()
                arg = None
            else:
                command = line[:i].upper()
                arg = line[i+1:].strip()
            max_sz = (self.command_size_limits[command]
                        if self.extended_smtp else self.command_size_limit)
            if sz > max_sz:
                self.push('500 5.5.2 Error: line too long.')
                return
            method = getattr(self, 'smtp_' + command, None)
            if not method:
                self.push(
                    '500 5.5.1 Error: command "%s" not recognized' % command)
                return
            method(arg)
            return
        else:
            if self.smtp_state != self.DATA:
                self.push('451 4.5.0 Internal confusion')
                self.num_bytes = 0
                return
            if self.data_size_limit and self.num_bytes > self.data_size_limit:
                self.push('552 5.3.4 Error: Too much mail data')
                self.num_bytes = 0
                return
            # Remove extraneous carriage returns and de-transparency according
            # to RFC 5321, Section 4.5.2.
            data = []
            for text in line.split(self._linesep):
                if text and text[0] == self._dotsep:
                    data.append(text[1:])
                else:
                    data.append(text)
            self.received_data = self._newline.join(data)
            args = (self.peer, self.mailfrom, self.rcpttos, self.received_data)
            kwargs = {}
            if not self._decode_data:
                kwargs = {
                    'mail_options': self.mail_options,
                    'rcpt_options': self.rcpt_options,
                }

            # EEH MODIFICATION
            kwargs["greeting"] = self.seen_greeting
            if hasattr(self, "cipher"):
                kwargs["cipher"] = self.cipher

            self.sleep(self.wake_data, self.smtp_server.process_message,
                       args, kwargs)



    def wake_data(self, future):
        self.in_background = False
        self._set_post_data_state()

        try:
            status = future.result()
        except:  # Must be as broad
            if hasattr(self.smtp_server, "logger"):
                self.smtp_server.logger.exception("Error in channel:")
            else:
                self.handle_error()  # Close connection, print to stdout
                return

            status = '554 5.5.0 Server error. Please contact admin.'

        if status is not None:
            self.push(status)
        else:
            self.push('250 2.0.0 OK')


    def sleep(self, continuation, fun, args, kwargs):
        self.in_background = True
        future = executor.submit(fun, *args, **kwargs)
        future.add_done_callback(self.wake_data)


class StartTLSFutureChannel(FutureChannel, StartTLSChannel):
    pass  # All work done :)
