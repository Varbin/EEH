import pytest
from EEHlib.delivery.base import BaseDelivery

def test_delivery():
    with pytest.raises(NotImplementedError):
        BaseDelivery({}, None).deliver("","","","")
        
if __name__ == "__main__":
    import __main__
    for i in dir(__main__):
        if i.startswith("test_"):
            print("---", i)
            eval(i).__call__()
