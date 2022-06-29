#!/usr/bin/env python

# The version as used in the setup.py and the docs conf.py
__version__ = "0.0.2"

# for command line
from jetend.modules.jmWind import WindServer

# include Package methods

# ---- [methods] --- #
from .Decoration import depreciated_method

# ---- [depreciated] --- #
from extended.wrapper.Log import get_logger

# ---- [definition] --- #


def warning(message, category=None, stacklevel=1, source=None):
    from traceback import extract_stack, FrameSummary
    from warnings import warn as warnings_warn
    for tb_info in extract_stack():
        assert isinstance(tb_info, FrameSummary)
        warnings_warn('[warning]: {} {} {}'.format(tb_info.filename, tb_info.lineno, tb_info.line))
    warnings_warn(message='[warning]: {}'.format(message), category=category, stacklevel=stacklevel, source=source)
