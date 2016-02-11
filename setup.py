# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

try:
    long_description = open("README.md").read()
except IOError:
    long_description = ""

setup(
    name="py-Gift",
    version="0.1",
    description="GIFT parser in python that parses a Gift source code and loads data in a Question/Answer model for further use in an application",
    license="AGPL",
    author="Marc Tommasi - UdL/INRIA",
    packages=find_packages(),
    install_requires=['yattag', 'i18n', 're'],
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
    ]
)
