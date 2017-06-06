import pytest
import mailbox

class MockBox:
    status = -1
    def __init__(self, path, create):
        pass

    def lock(self):
        pass

    def add(self, message):
        MockBox.status += 1
        if MockBox.status == 0:
            pass
        elif MockBox.status == 1:
            raise mailbox.ExternalClashError
        else:
            raise Exception

    def unlock(self):
        pass

    def close(self):
        pass


from EEHlib.delivery import filesystem
filesystem.mailbox.MockBox = MockBox
Delivery = filesystem.Delivery

def test_delivery():
    d = Delivery({"Mailboxformat":"MockBox", "Path":""})
    assert d.deliver("","","","")
    assert not d.deliver("","","","")
    assert not d.deliver("","","","")
