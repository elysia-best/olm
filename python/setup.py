# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools.command.build_ext import build_ext
import sys


class BuildExt(build_ext):
    def finalize_options(self):
        build_ext.finalize_options(self)
        if sys.platform == "win32":
            self.compiler = "mingw32"


setup(
    cffi_modules=["olm_build.py:ffibuilder"],
    cmdclass={"build_ext": BuildExt},
)
