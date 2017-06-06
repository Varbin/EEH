import pytest
from EEHlib.delivery.base import BaseDelivery

def test_delivery():
    with pytest.raises(NotImplementedError):
        BaseDelivery({}, None).deliver("","","","")
