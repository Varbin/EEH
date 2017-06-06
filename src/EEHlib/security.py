import grp
import os
import pwd


"""
Security helpers for EEH.
"""


def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        raise Exception("Cannot drop privileges! Not running as root!")

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(gid_name).gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    if hasattr(os, "setresgid"):
        os.setresgid(running_gid, running_gid, running_gid)
    os.setgid(running_gid)
    if hasattr(os, "setresuid"):
        os.setresuid(running_uid, running_uid, running_uid)
    os.setuid(running_uid)

    # Ensure a very conservative umask
    os.umask(0o077)
