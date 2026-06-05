# -*- coding: utf-8 -*-
from setuptools import setup
import sys

setup(
    cffi_modules=["olm_build.py:ffibuilder"],
)
