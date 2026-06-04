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

# Try to build with cmake first, fall back to GNU make
try:
    subprocess.run(
        ["cmake", ".", "-Bbuild", "-DBUILD_SHARED_LIBS=NO"],
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
        subprocess.run(["gmake", "static"], cwd="libolm", check=True)
    except FileNotFoundError:
        # some systems have GNU make installed without the leading "g"
        # so give that a try (though this may fail if it isn't GNU make)
        subprocess.run(["make", "static"], cwd="libolm", check=True)

ffibuilder.set_source(
    "_libolm",
    r"""
        #include <olm/olm.h>
        #include <olm/inbound_group_session.h>
        #include <olm/outbound_group_session.h>
        #include <olm/pk.h>
        #include <olm/sas.h>
    """,
    libraries=["olm"],
    library_dirs=[os.path.join("libolm", "build")],
    extra_compile_args=compile_args,
    extra_link_args=link_args,
    source_extension=".cpp", # we need to link the C++ standard library, so use a C++ extension
)

# Run C preprocessor on the headers to resolve #ifdef, #define, #include etc.
# that cffi's cdef parser cannot handle.
preprocess_input = (
    '#define OLM_STATIC_DEFINE\n'
    '#include "olm/olm.h"\n'
    '#include "olm/pk.h"\n'
    '#include "olm/sas.h"\n'
)


def _find_cc():
    """Find a working C compiler for preprocessing headers."""
    for cc in ["cc", "gcc", "clang"]:
        try:
            subprocess.run([cc, "--version"], capture_output=True, check=True)
            return cc
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("No working C compiler found (tried cc, gcc, clang)")


def _strip_attributes(text):
    """Strip GCC/Clang __attribute__((...)) with support for nested parens."""
    MATCH_LIST=[
        "__attribute__((__aligned__(__alignof__(long long))))",
        "__attribute__((__aligned__(__alignof__(long double))))"
    ]
    for match in MATCH_LIST:
        text = text.replace(match, "")
    return text


def _cpp(preprocess_input, include_dir):
    """Preprocess a C header string and return cleaned declarations.

    Uses the C preprocessor to expand macros and includes, then strips
    compiler-specific syntax that cffi's pycparser cannot handle.
    """
    cc = _find_cc()
    result = subprocess.run(
        [cc, "-E", "-P", f"-I{include_dir}", "-"],
        input=preprocess_input,
        capture_output=True,
        text=True,
        check=True,
    )
    return _strip_attributes(result.stdout)


ffibuilder.cdef(_cpp(preprocess_input, os.path.join(PATH, "include")), override=True)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
