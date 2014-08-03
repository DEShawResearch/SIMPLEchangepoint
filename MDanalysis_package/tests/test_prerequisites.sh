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

INCLUDE_PROBLEMS=0
LIB_PROBLEMS=0
PREREQ_PROBLEMS=0



echo 'Testing config.sh'

source ../config.sh

echo; echo 'Searching for headers'
if [ -f $SQLITE_INCLUDE/sqlite3.h ]
then
    echo "Found sqlite3.h (SQLITE_INCLUDE is OK)"
else
    echo "Couldn't find sqlite3.h in SQLITE_INCLUDE=$SQLITE_INCLUDE"
    INCLUDE_PROBLEMS=1
fi

if [ -f $PYTHON_INCLUDE/Python.h ]
then
    echo "Found Python.h (PYTHON_INCLUDE is OK)"
else
    echo "Couldn't find Python.h in PYTHON_INCLUDE=$PYTHON_INCLUDE"
    INCLUDE_PROBLEMS=1
fi
 
if [ -d $BOOST_INCLUDE/boost ]
then
    echo "Found boost headers (BOOST_INCLUDE is OK)"
else
    echo "Couldn't find boost subdirectory in BOOST_INCLUDE=$BOOST_INCLUDE"
    INCLUDE_PROBLEMS=1
fi

if [ -d $NUMPY_INCLUDE/numpy ]
then
    echo "Found numpy headers (NUMPY_INCLUDE is OK)"
else
    echo "Couldn't find numpy subdirectory in NUMPY_INCLUDE=$NUMPY_INCLUDE"
    INCLUDE_PROBLEMS=1
fi

if [ -d $LPSOLVE_INCLUDE/lp_solve ]
then
    echo "Found lp_solve headers (LPSOLVE_INCLUDE is OK)"
else
    echo "Couldn't find lp_solve subdirectory in LPSOLVE_INCLUDE=$LPSOLVE_INCLUDE"
    INCLUDE_PROBLEMS=1
fi

if [ $INCLUDE_PROBLEMS -eq "1" ]
then
    echo "ERROR: found one or more problems with header files.  Edit config.sh."
else
    echo "OK:    found all header files."
fi



echo; echo 'Searching for shared libraries'

# use gcc to resolve shared libraries
SQLITE_FOUND=0 && gcc -L${SQLITE_LIB} -l${lSQLITE} -shared 2>/dev/null \
    && SQLITE_FOUND=1
PYTHON_FOUND=0 && gcc -L${PYTHON_LIB} -l${lPYTHON} -shared 2>/dev/null \
    && PYTHON_FOUND=1
BOOST_FOUND=0 && gcc -L${BOOST_LIB} -lboost_python -shared 2>/dev/null \
    && BOOST_FOUND=1
LPSOLVE_FOUND=0 && gcc -L${LPSOLVE_LIB} -l${lLPSOLVE} -shared 2>/dev/null \
    && LPSOLVE_FOUND=1


if [ $SQLITE_FOUND -eq "1" ]
then
    echo "Resolved -l${lSQLITE} (SQLITE_LIB is OK)"
else
    echo "Couldn't resolve -l${lSQLITE} (lSQLITE=$lSQLITE) in SQLITE_LIB=$SQLITE_LIB"
    LIB_PROBLEMS=1
fi

if [ $PYTHON_FOUND -eq "1" ]
then
    echo "Resolved -l${lPYTHON} (PYTHON_LIB is OK)"
else
    echo "Couldn't resolve -l${lPYTHON} (lPYTHON=$lPYTHON) in PYTHON_LIB=$PYTHON_LIB"
    LIB_PROBLEMS=1
fi

if [ $BOOST_FOUND -eq "1" ]
then
    echo "Resolved -lboost_python (BOOST_LIB is OK)"
else
    echo "Couldn't resolve -lboost_python in BOOST_LIB=$BOOST_LIB"
    LIB_PROBLEMS=1
fi

if [ $LPSOLVE_FOUND -eq "1" ]
then
    echo "Resolved -l${lLPSOLVE} (LPSOLVE_LIB is OK)"
else
    echo "Couldn't resolve -l${lLPSOLVE} in LPSOLVE_LIB=$LPSOLVE_LIB"
    LIB_PROBLEMS=1
fi

if [ -f $NUMPY_LIB/multiarray.so ]
then
    echo "Found multiarray.so (NUMPY_LIB is OK)"
else
    echo "Couldn't find multiarray.so in NUMPY_LIB=$NUMPY_LIB"
    LIB_PROBLEMS=1
fi

if [ $LIB_PROBLEMS -eq "1" ]
then
    echo "ERROR: found one or more problems with shared libraries.  Edit config.sh."
else
    echo "OK:    found all shared libraries."
fi


echo; echo 'Testing Python prerequisites'
HAVE_PYTABLES=0 && \
    $python -c 'import tables' 2>/dev/null 1>/dev/null && \
    HAVE_PYTABLES=1

HAVE_SCIPY=0 && \
    $python -c 'import scipy' 2>/dev/null 1>/dev/null && \
    HAVE_SCIPY=1

HAVE_NUMPY=0 && \
    $python -c 'import numpy' 2>/dev/null 1>/dev/null && \
    HAVE_NUMPY=1

if [ $HAVE_PYTABLES -eq "1" ]
then
    echo 'Found PyTables package (tables)'
else
    echo "Couldn't find PyTables package (tables)"
    PREREQ_PROBLEMS=1
fi

if [ $HAVE_SCIPY -eq "1" ]
then
    echo 'Found SciPy package (scipy)'
else
    echo "Couldn't find SciPy package (scipy)"
    PREREQ_PROBLEMS=1
fi

if [ $HAVE_NUMPY -eq "1" ]
then
    echo 'Found NumPy package (numpy)'
else
    echo "Couldn't find NumPy package (numpy)"
    PREREQ_PROBLEMS=1
fi

if [ $PREREQ_PROBLEMS -eq "1" ]
then
    echo "ERROR: one or more prerequisites were not found.  Check that"
    echo "       the tables, numpy, and scipy Python packages (directories"
    echo "       containing __init__.py) are installed and on your "
    echo "       PYTHONPATH."
else
    echo "OK:    Found all prerequisites."
fi

echo;
if [ $INCLUDE_PROBLEMS -eq "0" ] && [ $LIB_PROBLEMS -eq "0" ] && [ $PREREQ_PROBLEMS -eq "0" ]
then
    echo "Found all requirements (header files, shared libraries, and"
    echo "prerequisites.)  Build should succeed."
    echo;
    exit 0
else
    echo "Found one or more errors with required software."
    echo;
    exit 1
fi
