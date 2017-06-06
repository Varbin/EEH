#!python3
from setuptools import setup, find_packages
from os import path

with open(path.join(path.dirname(__file__), "src/EEHlib/version.py")) as version_pkg:
    exec(version_pkg.read())

setup(
    name="EEH",
    version=__version__,
    package_dir = {'': 'src'},
    py_modules=['EEH'],
    packages=find_packages('src', include="*"),
    install_requires=[
        "dnspython", "click"],
    extra_requires={
        "ldap": ["ldap3>=2.0.0"],
        "spam": ["antispam"],
        "test": ["pytest"],
        },
    entry_points='''
        [console_scripts]
        EEH=EEH:main
    ''',
    
    )
