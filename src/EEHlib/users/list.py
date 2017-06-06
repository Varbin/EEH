from .base import BaseDriver
from time import time
import os.path

class Driver(BaseDriver):
    last_update = 0
    wl_users = []
    bl_users = []

    def __init__(self, config, domains=[], **kwargs):
        self.whitelist = config["Allow users file"]
        self.blacklist = config["Deny users file"]
        self.domains = domains
        self.update_after = int(config["Update after"])

        for file in self.whitelist, self.blacklist:
            if not os.path.isfile(file):
                with open(file, "w"):
                    pass


    def update(self):
        wl_users = []

        with open(self.whitelist) as wlf:
            for user in wlf.readlines():
                if not user.startswith("#"):
                    if user.strip():
                        wl_users.append(user.strip())

        bl_users = []
        with open(self.blacklist) as blf:
            for user in blf.readlines():
                if not user.startswith("#"):
                    if user.strip():
                        bl_users.append(user.strip())

        self.wl_users = wl_users
        self.bl_users = bl_users

        return True

    def update_if_required(self):
        if time() - self.last_update > self.update_after:
            self.last_update = time()
            return self.update()
        return None

    def is_accepted_user(self, user):
        self.update_if_required()
        return ((not self.wl_users or user in self.wl_users) and
                user not in self.bl_users)

    def resolve_user(self, user):
        return [user]

    
