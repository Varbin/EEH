from configparser import ConfigParser
from EEHlib.config import config

def test_config_configparser():
    assert isinstance(config, ConfigParser)
    
if __name__ == "__main__":
    import __main__
    for i in dir(__main__):
        if i.startswith("test_"):
            print("---", i)
            eval(i).__call__()
