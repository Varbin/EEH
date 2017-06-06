import pytest
from EEHlib.delivery.dummy import Delivery

def test_delivery():
    assert Delivery({}).deliver("","","","")
