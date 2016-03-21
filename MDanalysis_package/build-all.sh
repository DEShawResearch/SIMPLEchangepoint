#!/usr/bin/env bash

# This script builds the molfile, msys, and periodicfix Python
# extensions needed by the SIMPLE MD Analysis scripts. You will need
# to specify the paths to various header files and libraries in
# config.sh to build on your system.  You should not have to edit this
# file.

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

opt_j=1
opt_p=${PWD}
opt_b=0

while getopts ":j:p:b" opt ; do
    case $opt in
        j) opt_j=$OPTARG;;
        p) opt_p=$OPTARG;;
	b) opt_b=1;;
        \?) echo "invalid option -$OPTARG" 1>&2 ; exit 1;;
         :) echo "option -$OPTARG requires an option" 1>&2; exit 1;;
    esac
done

set -e

source config.sh

pushd tests
echo 'Testing system configuration before building...'
./test_prerequisites.sh
echo
source test_optional_software.sh
echo
popd

PREFIX=$(readlink -f $opt_p)
mkdir -p $PREFIX
PATH=$PATH:$PREFIX/bin
PYTHONPATH=$PYTHONPATH:$PREFIX/lib/python:$PREFIX/lib/python2.7/site-packages
echo "Installing in PREFIX=$PREFIX"

pushd src

# SIMPLE_changepoint core package
PREFIX=$PREFIX CORE_PACKAGE_FILES=$CORE_PACKAGE_FILES ./build-changepoint-core.sh

# D. J. Berstein's primegen (an msys prereq)
# primegen is public domain software
PREFIX=$PREFIX ./build-primegen.sh

# Scons build system (used for subsequent packages)
# scons-local is distributed by the SCons foundation under the MIT
# license
mkdir -p scons-local
pushd scons-local
tar -xvf ../scons-local-2.3.0.tar.gz
SCONSLOCAL="$python $PWD/scons.py"
popd

# Build frameset (a molfile prereq)
OBJDIR=$OBJDIR PREFIX=$PREFIX opt_j=$opt_j ./build-frameset.sh

# Build fastjson (an msys prereq)
tar -xf fastjson-1.5.1-src.tar.gz
pushd fastjson-1.5.1
CCFLAGS="-O3 -g -Wall -fPIC"
LINKFLAGS="-O3 -fPIC"
CCFLAGS=$CCFLAGS LINKFLAGS=$LINKFLAGS $SCONSLOCAL -j$opt_j install OBJDIR=objs  PREFIX=$PREFIX 
popd

# g++ flags
IBOOST="-I$BOOST_INCLUDE"
LBOOST="-L$BOOST_LIB:-Wl,-rpath,$BOOST_LIB" # -lboost_python -lboost_thread -lboost_iostreams -lboost_program_options"
IPYTHON="-I$PYTHON_INCLUDE"
LPYTHON="-L$PYTHON_LIB:-Wl,-rpath,$PYTHON_LIB" # -lpython
INUMPY="-I$NUMPY_INCLUDE"
ISQLITE="-I$SQLITE_INCLUDE"
LSQLITE="-L$SQLITE_LIB:-Wl,-rpath,$SQLITE_LIB" # -lsqlite3
ILPSOLVE="-I$LPSOLVE_INCLUDE"
LLPSOLVE="-L$LPSOLVE_LIB:-Wl,-rpath,$LPSOLVE_LIB" # -llpsolve

# Clean the compiler environment
LDFLAGS=""
CPPFLAGS=""

# Set up Python for DESRES-style scons build and unit-testing
export PYTHONPATH=$PWD/sconsutils:$PYTHONPATH

# Build molfile
tar -xf molfile-1.10.15-src.tar.gz
pushd molfile-1.10.15
DESRES_MODULE_CPPFLAGS="$IBOOST:$IPYTHON:$INUMPY:$ISQLITE"
DESRES_MODULE_LDFLAGS="$LBOOST:$LPYTHON:$LNUMPY:$LSQLITE"
DESRES_MODULE_CPPFLAGS=$DESRES_MODULE_CPPFLAGS DESRES_MODULE_LDFLAGS=$DESRES_MODULE_LDFLAGS $SCONSLOCAL -j$opt_j install  PREFIX=$PREFIX 
echo; echo 'Testing molfile'
$python tests/ut.py
popd

# Build periodicfix
tar -xf periodicfix-2.4.7-src.tar.gz
pushd periodicfix-2.4.7
DESRES_MODULE_CPPFLAGS="$IBOOST:$IPYTHON:$INUMPY"
DESRES_MODULE_LDFLAGS="$LBOOST:$LPYTHON:$LNUMPY"
DESRES_MODULE_CPPFLAGS=$DESRES_MODULE_CPPFLAGS DESRES_MODULE_LDFLAGS=$DESRES_MODULE_LDFLAGS $SCONSLOCAL -j$opt_j install  PREFIX=$PREFIX 
echo; echo 'Testing periodicfix'
$python test/test_pf.py
popd

# Build msys
tar -xf msys-1.7.52-src.tar.gz
cp -f sconsutils/msys_SConscript msys-1.7.52/SConscript # clobber!
cp -f sconsutils/msys_tools_SConscript msys-1.7.52/tools/SConscript # clobber!
cp -f sconsutils/msys_tests_ut.py msys-1.7.52/tests/ut.py # clobber!
patch msys-1.7.52/src/analyze/bond_orders.cxx < patches/msys_bond_orders.patch
patch msys-1.7.52/SConscript < patches/msys_SConscript.patch
pushd msys-1.7.52

DESRES_MODULE_CPPFLAGS="$IBOOST:$IPYTHON:$INUMPY:$ISQLITE:$ILPSOLVE:-I${PREFIX}/include"
DESRES_MODULE_LDFLAGS="$LBOOST:$LPYTHON:$LNUMPY:$LSQLITE:$LLPSOLVE:-L${PREFIX}/lib:-Wl,-rpath,${PREFIX}/lib"
DESRES_MODULE_LDLIBS="-l$lPYTHON:-l$lSQLITE:-lfastjson:-lprimegen:-l$lLPSOLVE"
MSYS_VERSION=1.7.52 DESRES_MODULE_CPPFLAGS=$DESRES_MODULE_CPPFLAGS DESRES_MODULE_LDFLAGS=$DESRES_MODULE_LDFLAGS DESRES_MODULE_LDLIBS=$DESRES_MODULE_LDLIBS $SCONSLOCAL -j$opt_j install  PREFIX=$PREFIX MSYS_WITHOUT_INCHI=1
echo; echo 'Testing msys'
$python tests/ut.py
popd

popd

# Unpack documentation
pushd docs
tar -xvf html.tar.gz
popd

echo; echo 'Installing changepoint MD analysis software'
rsync -av --update $PWD/scripts/ $PREFIX/bin
rsync -av --update $PWD/lib-python/ $PREFIX/lib/python

# Need to edit script on the fly
dcd=$PREFIX/bin/detect_changed_distances
sed "s/SED_REPLACES_THIS/$python/" $dcd >$dcd.tmp
mv -f $dcd.tmp $dcd
chmod +x $dcd
chmod -w $dcd

echo; echo 'Testing detect_changed_distances'
python=$python EXAMPLESDIR=examples tests/test_detect_changed_distances.sh

echo;
if [ $HAVE_OPTIONAL -eq "1" ]
then
    echo "Testing VMD-based visualzation"
    tests/test-vmd.sh
else
    echo "Optional software not found: skipping VMD-based visualization tests"
fi

echo;
echo "Be sure to add the following to your .bashrc or equivalent:"
echo "  "PATH=$PREFIX/bin:'$PATH'
echo "  "PYTHONPATH=$PREFIX/lib/python:$PREFIX/lib/python2.7/site-packages:'$PYTHONPATH'
