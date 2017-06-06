class BaseDelivery:
    def __init__(self, config, logger=None):
        pass

    def deliver(self, user, domain, message, from_):
        raise NotImplementedError
