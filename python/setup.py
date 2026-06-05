# -*- coding: utf-8 -*-
from setuptools import setup
import sys

setup(
    cffi_modules=["olm_build.py:ffibuilder"],
    build={
        "compiler": "mingw32" if (sys.platform == "win32") else "unix",
    }
)
