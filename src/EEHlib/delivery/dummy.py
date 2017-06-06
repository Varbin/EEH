from .base import BaseDelivery
import logging


class Delivery(BaseDelivery):
    def __init__(self, config, logger=logging.getLogger("EEH.Delivery")):
        super().__init__(config)

        logger.info("Delivery method: Dummy")
        self.logger = logger

    def deliver(self, user, domain, message, sender):
        self.logger.info(("Incoming and unsaved message to {}[@{}], "
                          "message length {}").format(user,
                                                      domain,
                                                      str(len(str(message)))))
        return True
