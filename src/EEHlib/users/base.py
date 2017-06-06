class BaseDriver:
    def __init__(self, domains, **kwargs):
        pass

    def update(self):
        return False

    def update_if_required(self):
        return self.update()

    def is_accepted_user(self, user):
        return False

    def resolve_user(self, user):
        return []

