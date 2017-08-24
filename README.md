# pygiftparser
[Gift](http://microformats.org/wiki/gift) parser in python with HTML generation. 

[![Build Status](https://travis-ci.org/mtommasi/pygiftparser.svg?branch=master)](https://travis-ci.org/mtommasi/pygiftparser)
[![Coverage Status](https://coveralls.io/repos/github/mtommasi/pygiftparser/badge.svg?branch=master)](https://coveralls.io/github/mtommasi/pygiftparser?branch=master)

## Requirements

- python3
- markdown
- markdownSuperscript
- yattag

(bs4 to run the test suite)

## Install

```
pip install pygiftparser
```

Import it in your application like this
```
from pygiftparser import parser 
```

## Internationalization

In order to generate the translation files, just launch

```
xgettext --language=Python --keyword=_ --output=po/pygiftparser.pot `find . -name "*.py"`
```

then use `poedit` or use `msginit` (example below) and translate strings from the generated catalog

```
msginit --input=pygift.pot --locale=fr
```

Then put mo files in the `locale` directory. (Example with the `fr_FR` locale)

```
cp po/fr_FR.mo ../share/locale/fr_FR/LC_MESSAGES/pygiftparser.mo
``` 

## Notes

list of numerical answers is not covered
