#!/usr/bin/env python

# The version as used in the setup.py and the docs conf.py
__version__ = "0.0.1"

# include Package Modules
from .EventEngine import EventEngine, EventObject
from .Exceptions import (
    ParamMissingError, ParamNoContentError, ParamOutOfRangeError, ParamTypeError,
    ValueTypeError,
)
from .Interface import AbstractPersistObject

# include folder Package Modules
from .data.CountingDict import CountingDict
from .data.ObjectDict import ObjectDict

from .persist.Dict import TextDict, TextObjDict

from .wrapper.Shelve import ShelveWrapper

# include Package methods
from .Decoration import depreciated_method
from .Logger import get_logger
from .Path import Path

# ---- [depreciated] --- #
DataDict = ObjectDict


def is_chinese_char(char: str):
    assert len(char) == 1
    if '\u4e00' <= char <= '\u9fff':
        return True
    else:
        return False


def is_english_char(char: str):
    import re
    assert len(char) == 1
    if re.match(r'[a-zA-Z]', char, re.I):
        return True
    else:
        return False
