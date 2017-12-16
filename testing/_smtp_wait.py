from smtplib import SMTP as _SMTP
import time

def SMTP(*args, **kwargs):
    start = time.time()
    error = True
    while error and time.time() - start <= 15:
        try:
            s = _SMTP(*args, **kwargs)
        except ConnectionRefusedError:
            continue
        else:
            error = False
    if error:
        raise ConnectionRefusedError
    return s
