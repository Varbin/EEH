import asyncore
import ssl

class TLSHandshaker(asyncore.dispatcher):
    want_write = True
    want_read = True

    def __init__(self, sock, parent, map=None):
        self.parent = parent
        asyncore.dispatcher.__init__(self, sock, map)

    def writable(self):
        return self.want_write

    def readable(self):
        return self.want_read

    def do_handshake(self):
        try:
            self.socket.do_handshake()
        except ssl.SSLWantReadError:
            self.want_write = False
            self.want_read = True
        except ssl.SSLWantWriteError:
            self.want_write = True
            self.want_read = False
        else:
            self.del_channel()
            self.parent.replace_connection(self.socket)

    handle_read = handle_write = do_handshake  # Try it on every R/W
