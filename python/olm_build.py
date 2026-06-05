# -*- coding: utf-8 -*-

# libolm python bindings
# Copyright © 2018 Damir Jelić <poljar@termina.org.uk>
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted, provided that the
# above copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
# RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
# CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import os
import sys
import re
import subprocess

from cffi import FFI

ffibuilder = FFI()
PATH = os.path.dirname(__file__)

DEVELOP = os.environ.get("DEVELOP")

compile_args = ["-Ilibolm/include"]
link_args = []

if DEVELOP and DEVELOP.lower() in ["yes", "true", "1"]:
    link_args.append('-Wl,-rpath=../build')

cxx_compiler = "g++"
c_compiler = "gcc"
if sys.platform == "win32":
    cxx_compiler = "x86_64-w64-mingw32-g++"
    c_compiler = "x86_64-w64-mingw32-gcc"
elif sys.platform == "linux":
    cxx_compiler = "g++"
    c_compiler = "gcc"
elif sys.platform == "darwin":
    cxx_compiler = "clang++"
    c_compiler = "clang"
else:
    raise RuntimeError(f"Unsupported platform: {sys.platform}")

# Try to build with cmake first, fall back to GNU make
try:
    subprocess.run(
        ["cmake", ".", "-Bbuild", "-DBUILD_SHARED_LIBS=NO", "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_CXX_COMPILER={cxx_compiler}", f"-DCMAKE_C_COMPILER={c_compiler}", "-G", "Ninja"],
        cwd="libolm", check=True,
    )
    subprocess.run(
        ["cmake", "--build", "build"],
        cwd="libolm", check=True,
    )
except FileNotFoundError:
    try:
        # try "gmake" first because some systems have a non-GNU make
        # installed as "make"
        subprocess.run(["gmake", "CC=" + c_compiler, "CXX=" + cxx_compiler, "static"], cwd="libolm", check=True)
    except FileNotFoundError:
        # some systems have GNU make installed without the leading "g"
        # so give that a try (though this may fail if it isn't GNU make)
        subprocess.run(["make", "CC=" + c_compiler, "CXX=" + cxx_compiler, "static"], cwd="libolm", check=True)

ffibuilder.set_source(
    "_libolm",
    r"""
        #include <olm/olm.h>
        #include <olm/inbound_group_session.h>
        #include <olm/outbound_group_session.h>
        #include <olm/pk.h>
        #include <olm/sas.h>
    """,
    libraries=['olm'],
    library_dirs=[os.path.join("libolm", "build"),],
    extra_compile_args=compile_args,
    extra_link_args=link_args,
    source_extension=".cpp", # we need to link the C++ standard library, so use a C++ extension
)

with open(os.path.join(PATH, "interface-include/olm/error.h")) as f:
    ffibuilder.cdef(f.read(), override=True)

with open(os.path.join(PATH, "interface-include/olm/olm.h")) as f:
    ffibuilder.cdef(f.read(), override=True)

with open(os.path.join(PATH, "interface-include/olm/pk.h")) as f:
    ffibuilder.cdef(f.read(), override=True)

with open(os.path.join(PATH, "interface-include/olm/sas.h")) as f:
    ffibuilder.cdef(f.read(), override=True)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
