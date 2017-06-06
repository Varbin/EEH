from configparser import ConfigParser
from EEHlib.config import config

def test_config_configparser():
    assert isinstance(config, ConfigParser)
