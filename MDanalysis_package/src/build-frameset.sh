#!/usr/bin/env bash
#
# This script builds the frameset extension needed by molfile.

# Copyright 2012-2014, D. E. Shaw Research.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions, and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions, and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# * Neither the name of D. E. Shaw Research nor the names of its
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

set -e

source ../config.sh

# Clean the compiler environment
export LDFLAGS="" #"-L$PREFIX/lib -Wl,-rpath,$PREFIX/lib"
export CPPFLAGS="" #"-I$PREFIX/include"

tar -xf frameset-from-Desmond-3.4.0.2-benchmark.tar.gz
pushd frameset

cat <<EOF > conf.py
if EXTRA_C_FLAGS == None: EXTRA_C_FLAGS = ''
if EXTRA_CC_FLAGS == None: EXTRA_CC_FLAGS = ''
if EXTRA_LINK_FLAGS == None: EXTRA_LINK_FLAGS = ''
if EXTRA_LIBS == None: EXTRA_LIBS = ''

if EXTRA_INCLUDE_PATH == None: EXTRA_INCLUDE_PATH = ''
if EXTRA_LIBRARY_PATH == None: EXTRA_LIBRARY_PATH = ''

USE_BFD=False

THREADS = 'POSIX'
WITH_MPI = 0

prefix = "$PREFIX"

EXTRA_INCLUDE_PATH += ' $BOOST_INCLUDE'
EXTRA_INCLUDE_PATH += ' $PYTHON_INCLUDE'
EXTRA_INCLUDE_PATH += ' $NUMPY_INCLUDE'
EXTRA_INCLUDE_PATH += ' $SQLITE_INCLUDE'

EXTRA_LIBRARY_PATH += ' $BOOST_LIB'
EXTRA_LIBRARY_PATH += ' $PYTHON_LIB'
EXTRA_LIBRARY_PATH += ' $SQLITE_LIB'

EXTRA_LINK_FLAGS   += ' -Wl,-rpath,$BOOST_LIB'
EXTRA_LINK_FLAGS   += ' -Wl,-rpath,$PYTHON_LIB'
EXTRA_LINK_FLAGS   += ' -Wl,-rpath,$SQLITE_LIB'

EXTRA_LIBS += ' -lboost_iostreams -lboost_program_options -lboost_thread'
EXTRA_LIBS += ' -lboost_python -l${lPYTHON}'
EXTRA_LIBS += ' -lpcre'
EXTRA_LIBS += ' -l${lSQLITE}'

MPI_CPPFLAGS = "-pthread -DOMPI_SKIP_MPICXX" 
EOF

python ../scons-local/scons.py -j${opt_j} --user-conf=conf.py \
    install PREFIX=$PREFIX 
# OBJDIR=$OBJDIR
popd
