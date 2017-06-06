from .base import BaseDriver
from ldap3 import Connection
from ldap3.utils.conv import escape_bytes

ldap_escape = lambda s: escape_bytes(s.encode())

class Driver(BaseDriver):
    connection = None
    def __init__(self, config, domains=[], **kwargs):
        self.config = config

        self.user_base = config["user base"]
        self.user_query = config["user query"]
        self.user_name_attribute = config["user name attribute"]
        self.user_mail_attribute = config["user mail attribute"]

        self.group_base = config["group base"]
        self.group_query = config["group query"]
        self.group_member_attribute = config["group member attribute"]

        self.domains = domains


    def get_connection(self, c=None):
        if c is None:
            return Connection(self.config["server"], self.config["binddn"],
                              self.config["password"], True)
        else:
            return c

    def update(self):
        # Not needed (no caching yet)
        return True

    def _lookup_user(self, user_or_mail):
        c = self.get_connection()
        user_or_mail = ldap_escape(user_or_mail)
        query = self.user_query.format(user_or_mail)
        c.search(self.user_base, query, attributes=[
            self.user_mail_attribute, self.user_name_attribute])

        if c.entries:
            r = str(getattr(c.entries[0], self.user_name_attribute))
            c.unbind()
            return r
        else:
            return False

    def is_accepted_user(self, user):
        return bool(self._lookup_user(user))

    def _recursive_search(self, dn, resolved=[]):
        c = self.get_connection()
        if dn in resolved:
            return []
        resolved.append(dn)
        #print(repr(dn))
        c.search(dn, "(objectClass=*)", search_scope="BASE",
                    attributes=[self.group_member_attribute,
                               self.user_mail_attribute])
        mails = []
        if hasattr(c.entries[0], self.group_member_attribute):
            members = tuple(getattr(c.entries[0], self.group_member_attribute))
            for member in members:
                mails += self._recursive_search(member, resolved)
        if hasattr(c.entries[0], self.user_mail_attribute):
            for mail in getattr(c.entries[0], self.user_mail_attribute):
                if mail not in mails:
                    a =  self._lookup_user(mail)
                    if a:
                        mails.append(a)
                    else:
                        mails.append(mail)
        #print(resolved)
        c.unbind()
        return mails


    def resolve_user(self, user):
        c = self.get_connection()

        a = self._lookup_user(user)
        if a:
            return [a]
            

        group = ldap_escape(user)
        query = self.group_query % group

        if c.search(self.group_base, query, attributes=[
                self.group_member_attribute,
                self.user_mail_attribute]):
            #print("Search successfull:", query, c.entries[0].entry_dn)
            entry_dn = c.entries[0].entry_dn
            c.unbind()
            return self._recursive_search(entry_dn, [])

