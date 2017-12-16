import pytest
from EEHlib.delivery.dummy import Delivery

def test_delivery():
    assert Delivery({}).deliver("","","","")
    
if __name__ == "__main__":
    import __main__
    for i in dir(__main__):
        if i.startswith("test_"):
            print("---", i)
            eval(i).__call__()
