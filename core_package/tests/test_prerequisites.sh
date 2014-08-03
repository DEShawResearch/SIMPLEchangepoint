#/usr/bin/env bash

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

set +x

set +e # don't die if the python -c lines fail
source ../config.sh


INCLUDE_PROBLEMS=0
PREREQ_PROBLEMS=0

echo; echo 'Searching for headers specified by config.sh'
if [ -f $PYTHON_INCLUDE/Python.h ]
then
    echo "Found Python.h (PYTHON_INCLUDE is OK)"
else
    echo "Couldn't find Python.h in PYTHON_INCLUDE=$PYTHON_INCLUDE"
    INCLUDE_PROBLEMS=1
fi
 
if [ -d $NUMPY_INCLUDE/numpy ]
then
    echo "Found numpy headers (NUMPY_INCLUDE is OK)"
else
    echo "Couldn't find numpy subdirectory in NUMPY_INCLUDE=$NUMPY_INCLUDE"
    INCLUDE_PROBLEMS=1
fi

if [ $INCLUDE_PROBLEMS -eq "1" ]
then
    echo "ERROR: found one or more problems with header files.  Edit config.sh."
else
    echo "OK:    found all header files."
fi

 
echo; echo 'Testing python for installed packages'

HAVE_PYTABLES=0 && \
    $python -c 'import tables' 2>/dev/null 1>/dev/null && \
    HAVE_PYTABLES=1

HAVE_SCIPY=0 && \
    $python -c 'import scipy' 2>/dev/null 1>/dev/null && \
    HAVE_SCIPY=1

HAVE_NUMPY=0 && \
    $python -c 'import numpy' 2>/dev/null 1>/dev/null && \
    HAVE_NUMPY=1

if [ $HAVE_NUMPY -eq "1" ]
then
    echo 'Found Numpy package (numpy)'
else
    echo "Couldn't find Numpy package"
    PREREQ_PROBLEMS=1
fi

if [ $HAVE_SCIPY -eq "1" ]
then
    echo 'Found SciPy package (scipy)'
else
    echo "Couldn't find SciPy package"
    PREREQ_PROBLEMS=1
fi

if [ $PREREQ_PROBLEMS -eq "1" ]
then
    echo "ERROR: one or more prerequisites were not found.  Check that"
    echo "       the 'numpy' and 'scipy' Python packages (directories"
    echo "       containing __init__.py) are installed and on your "
    echo "       PYTHONPATH."
else
    echo "OK:    Found all required python packages."
fi

echo;
if [ $INCLUDE_PROBLEMS -eq "0" ] && [ $PREREQ_PROBLEMS -eq "0" ]
then
    echo "Found header files and prerequisites.  Build should succeed."
else
    echo "Found one or more errors with required software."
    exit 1
fi

echo; echo 'Searching for optional software'
HAVE_OPTIONAL="1"
if [ $HAVE_PYTABLES -eq "1" ]
then
    echo 'Found PyTables package (tables)'
else
    echo "Couldn't find PyTables package (tables)"
    HAVE_OPTIONAL="0"
fi

if [ $HAVE_OPTIONAL -eq "1" ]
then
    echo "OK:      found all optional software."
else
    echo "WARNING: some optional software was not found; VMD-based "
    echo "         visualization will not be available."
fi

set -e
