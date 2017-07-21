#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

try:
    long_description = open("README.rst").read()
except IOError:
    long_description = ""

LOCALEDIR=os.path.join('share','locale')
    
setup(
    name="pygiftparser",
    version="1.0",
    url="https://github.com/mtommasi/pygiftparser",
    description="GIFT parser in python that parses a Gift source code and loads data in a Question/Answer model for further use in an application",
    license="MIT",
    author="Marc Tommasi - UdL/INRIA",
    author_email="first.last@univ-lille.fr", 
    py_modules=['pygiftparser.parser', 'pygiftparser.i18n'],
    install_requires=['yattag', 'markdown', 'MarkdownSuperscript'],
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "Topic :: Text Processing"
    ],
    data_files = [(os.path.join('share', 'locale', lang, 'LC_MESSAGES'),
                   [os.path.join('share','locale', lang, 'LC_MESSAGES',
                                 'pygiftparser.mo')]) for lang in os.listdir(LOCALEDIR)]
)
