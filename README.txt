# Easy Email Host

[![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-☻-1EAEDB.svg)](https://saythanks.io/to/Varbin)

MDA with focus on:

 - easy configurability:
   - theoretically works without any configuration for single user setup
   - configuration is easy to learn
 - easy LDAP setup:
   - easy setup for mailinglists and users
 - easy deployment
   - Python ZIP Application with all dependencies
   - crossplatform (Windows, Posix)
   - delivery to all LMTP supporting local delivery agents and common mailboxes (Maildir, mbox)
 - easy privacy
   - supports STARTTLS
   - GPG support before saving is planned

EEH builds on Python's standart library's `smtpd` module adding STARTTLS, mailbox and LMTP delivery,
fixing Python issue 21783 (https://bugs.python.org/issue21783).

## Installation

So it's easy - how to install it?

### Basic

0. Get Python >= 3.4
1. Download EEH.pyz 
   - [to add]
2. Make it executable (not required on Windows):
   - `chmod +x /path/to/EEH.pyz`
3. Add it to autostart or services (differs from system to system)
4. Config path is (relative to EEH.pyz) `../EEH/` (on POSIX) or `./EEH/`(Windows)
5. Choose way to store mails:
   - Dummy, Filesystem or LMTP (for example to Dovecot)
6. Choose a user database:
   - File based or LDAP (for the latter see advanced topic)

## Changelog

### 1.1.0: First official release

 - Adds:
   - Message delivery is encapsulated in Python futures for overlapping IO.
 - Fixes:
   - Security //1 (see below)
   - Security //2 (see below)
   - Mail delivery impossible under following conditions, connection breaks after 30s
    (chain of bugs including Security #1 and Security #2):
     - Python 3.4
     - DNSBL not configured
 - Kown bugs:
   - SMTP `QUIT` command runs unexpectedly long.

### 1.0.1.4: First testing release

 - Known Bugs:
   - Security //1 (see below)
   - Security //2 (see below)


 - Adds:
   - Itself.

## Security

Beside DoS usable bugs in previous versions of EEH no other security related bugs are known.

### Vulnerabilities

 - **Security //1**:
   - Affected versions: <=1.0.1.4; Fixed in version: 1.1.0
   - Type: (d)DoS
   - Description: Blocking message delivery in main thread.
   - Requirements:
      - Depends on configuration, especially affected are setups with LMTP delivery and 
      LDAP user database setups are affected.
    - Severity: Medium, 5.9 (CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L)
 - **Security //2**:
    - Affected versions: <=1.0.1.4; Fixed in version: 1.1.0
    - Type: DoS
    - Description: 
      - Blocks everything for 30s if blocklist is not reachable.
      - After 30s a Timeout-exception is raised, closing the connection.
    - Requirements:
      - DNSBL is configured but a single (or more) lists are not reachable.
      - *No exploit required!*
    - Severity: Medium, 5.9 (CVSS:3.0/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:N/A:H)
    - Other: Result from Security //1