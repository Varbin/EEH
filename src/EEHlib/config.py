from configparser import ConfigParser

DEFAULT = """
[Network]
Host = 0.0.0.0
Port = 25

[Logging]
File = 
Level = INFO

[Security]
Allow defined domains only = yes
Privilege drop = no
Drop privileges to user = nobody
Drop privileges to group = nogroup
External delivery = yes
DNSBL =
Banner = ESMTP EEH ready.

[GPG]
PGP encrypt = no
PGP decrypt = no
Try multipart = no

[Performance]
Additional garbage collection = yes
Background threads = DEFAULT
msvcrt.heapmin = no

[Users]
Userdb type = List

[List]
Allow users file = users.allow
Deny users file = users.deny
Update after = 300

[LDAP]
server = localhost
binddn = cn=admin,dc=example,dc=org
password = 123456
user base = ou=users,dc=example,dc=org
user query = (&(|(uid={0})(mail={0}))(objectClass=inetOrgPerson)))
user mail attribute = mail
user name attribute = uid
group base = ou=mailinglists,dc=example,dc=org
group query = (&(cn=%%s)(objectClass=groupOfNames))
group member attribute = member

[Delivery]
Method = Filesystem
Domains = localhost.localdomain localhost {node} {fqdn}
fqdn override = 
data size limit = 50 Mi

[Dummy]

[Filesystem]
Mailboxformat = Maildir
Path = Mail

[LMTP]
Url = tcp://localhost:24
Enforce encryption = no

[STARTTLS]
enabled = no
certificate =
dedicated key =
ciphers =
curve =
dhparams =

[Encoding]
smtputf8 = yes
"""

config = ConfigParser()
config.read_string(DEFAULT)
    
