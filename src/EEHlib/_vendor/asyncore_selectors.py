import asyncore
import selectors

__version__ = "0.0.1-experimental-vendor"

socket_map = asyncore.socket_map


def fastpoll(timeout=0.0, map=None, selector_class=selectors.DefaultSelector):
    """
    Improved asyncore.poll / asyncore.poll2

    Uses the selectors module which selects the most efficient selector
    the OS / Python can offer.

    Examples:
     - select on Windows and old OS
     - poll on old OS without select (?)
     - Kqueue on modern BSD
     - Epoll on modern Linux
     - Devpoll on Solaris (Py >= 3.5)

    In result asyncore.loop may be better on older systems (and Windows), as
    selectors.*Selector does not support the third selector argument.
    """

    if map is None:
        map = socket_map

    if map:
        with selector_class() as selector:
        
            for fd, obj in list(map.items()):
                flags = 0
                if obj.readable():
                    flags |= selectors.EVENT_READ
                if obj.writable() and not obj.accepting:
                    flags |= selectors.EVENT_WRITE

                if flags:
                    selector.register(fd, flags)

            for key, event in selector.select(timeout):
                obj = map.get(key.fd)
                if obj is None:
                    continue
                try:
                    if event & selectors.EVENT_READ:
                        obj.handle_read_event()
                    if event & selectors.EVENT_WRITE:
                        obj.handle_write_event()
                except OSError as e:
                    if e.args[0] not in asyncore._DISCONNECTED:
                        obj.handle_error()
                    else:
                        obj.handle_close()
                except asyncore._reraised_exceptions:
                    raise
                except:
                    obj.handle_error()


def loop(timeout=30.0, use_poll=False, map=None, count=None,
         selector_class=selectors.DefaultSelector):
    """
    Improved event loop for asyncore. Uses asyncore_selector's fastpoll.
    Mostly backwards compatible. "use_poll" will be ignored. Instead
    use the "selector_class".
    """
    # use_poll is ignored

    if map is None:
        map = socket_map

    poll_fun = fastpoll

    if count is None:
        while map:
            poll_fun(timeout, map, selector_class)

    else:
        while map and count > 0:
            poll_fun(timout, map, selector_class)
            count -= 1
        
            
