from .base import BaseDelivery

import mailbox
import logging


class Delivery(BaseDelivery):
    def __init__(self, config, logger=logging.getLogger("EEH.Delivery")):
        super().__init__(config)

        logger.info("Delivery method: Filesystem")

        self.mailbox_format = getattr(mailbox, config["Mailboxformat"])
        self.mailbox_path = config["Path"]
        self.logger = logger

    def deliver(self, user, domain, message, from_):
        self.logger.info("Delivering message to: {}[@{}]".format(
            user, domain))

        message = mailbox.Message(message)

        success = True

        path = self.mailbox_path.format(user=user, domain=domain)
        user_mailbox = self.mailbox_format(path, create=True)

        self.logger.debug("Mailboxpath for {}[@{}] is: {}".format(
            user, domain, path))

        try:
            user_mailbox.lock()
            user_mailbox.add(message)
        except mailbox.ExternalClashError:
            success = False
            self.logger.warning(
                "Mailbox not available of user {user}: "
                "ExternalClash".format(user=user))
        except Exception as e:
            success = False
            self.logger.error(
                ("Mailbox not available of user {user}: "
                 "" + str(e) + " " + str(e.args)).format(user=user))
        else:
            self.logger.info("Delivery to {}[@{}] successful".format(
                user, domain))
        finally:
            user_mailbox.unlock()
            user_mailbox.close()

        return success
