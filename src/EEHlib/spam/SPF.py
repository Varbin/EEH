from dns.resolver import Resolver
import socket
import ipaddress

__version__ = "0.0.1"

PASS = "pass"
FAIL = "fail"
SOFTFAIL = "softfail"
NEUTRAL = "neutral"
PERMERROR = "permerror"
TEMPERROR = "temperror"
NONE = "none"

SMTP_PERM_FAIL = 550

statusmap = {
    PASS: (250, "sender SPF authorized"),
    FAIL: (SMTP_PERM_FAIL, "SPF fail - not authorized"),
    NEUTRAL: (250, "access neither permitted nor denied"),
    SOFTFAIL: (250, "domain owner discourages use of this host"),
    PERMERROR: (450, "permanent error"),
    TEMPERROR: (450, "temporary error"),
    NONE: (250, "equivocal SPF header"),
}


def handle_all(arg, domain):
    return lambda c: True


def handle_ip(arg, domain):
    def validate(c):
        try:
            c = socket.gethostbyname(c)
        except:
            return False

        if "/" in arg:
            return ipaddress.ip_address(c) in ipaddress.ip_network(
                arg, False)
        else:
            return c == arg

    return validate


def handle_a(arg, domain):
    if "/" in arg:
        arg, length = arg.split("/")
        network = True
    else:
        network = False

    if not arg:
        arg = domain

    ip = socket.gethostbyname(arg)

    if network:
        return handle_ip("/".join([ip, length]), domain)
    else:
        return handle_ip(ip, domain)


def handle_mx(arg, domain):
    if "/" in arg:
        arg, length = arg.split("/")
        network = True
    else:
        network = False

    if not arg:
        arg = domain

    a = Resolver().query(arg, "MX")
    ips = map(socket.gethostbyname,
              map(lambda c: c.exchange.to_text(True), a))

    if network:
        def validate(c):
            c = ipaddress.ip_address(socket.gethostbyname(c))
            o = False
            for i in ips:
                o |= c in ipaddress.ip_network(i+"/"+length, False)
            return o

        return validate
    else:
        return lambda c: socket.gethostbyname(c) in ips


def handle_ptr(arg, domain):
    if not arg:
        arg = domain

    def validate(c):
        try:
            name, aliases, ip = socket.gethostbyaddr(c)
        except OSError:
            return False
        hostnames = [name] + aliases

        for hostname in hostnames:
            try:
                res = socket.gethostbyname(hostname)
            except:
                continue
            else:
                if hostname.endswith(arg) and n == ip:
                    return True

        else:
            return False

    return validate


def handle_include(arg, domain):
    return lambda c: spf(arg, c)[1] != SMTP_PERM_FAIL


def handle_exp(arg, domain):
    return lambda c: False


def handle_exists(arg, domain):
    def validate(c):
        try:
            socket.gethostbyname(c)
        except:
            return False
        else:
            return True

    return validate


MECHANISMS = {
    "all": handle_all,
    "ip4": handle_ip,
    "ip6": handle_ip,
    "a": handle_a,
    "mx": handle_mx,
    "ptr": handle_ptr,
    "include": handle_include,
    "exists": handle_exists,
    "exp": handle_exp,
}


def spf(domain, greeting):
    r = Resolver()
    answers = r.query(domain, "TXT")
    for answer in answers:
        # print(answer.strings[0])
        if answer.strings[0].startswith(b"v=spf"):
            policy = answer.strings[0]
            break
    else:
        return (NEUTRAL, *statusmap[NEUTRAL])

    spfp = policy.decode().lower().split(" ")[1:]

    for action in spfp:

        if action.startswith("+"):
            action = action[1:]
            verb = PASS
        elif action.startswith("-"):
            action = action[1:]
            verb = FAIL
        elif action.startswith("~"):
            action = action[1:]
            verb = SOFTFAIL
        elif action.startswith("?"):
            action = action[1:]
            verb = NEUTRAL
        else:
            verb = PASS

        # print(action)

        if ":" in action:
            action, _, param = action.partition(":")
        elif "=" in action:
            action, _, param = action.partition("=")
        else:
            param = ""

        # print(param)

        if action == "redirect":
            return spf(param, greeting)
        elif action not in MECHANISMS:
            return (PERMERROR, *statusmap[PERMERROR])
        else:
            # print(verb, action, param, MECHANISMS[action](param, domain)(greeting))
            if MECHANISMS[action](param, domain)(greeting):
                return (verb, *statusmap[verb])

    else:
        return (NONE, *statusmap[NONE])
