#!/usr/bin/env bash

# This script builds the SIMPLE changepoint core files.  You will need
# to specify the paths to two header files in config.sh to build on
# your system.  You should not have to edit this file.

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


opt_p=${PWD}

while getopts ":p:p" opt ; do
    case $opt in
        p) opt_p=$OPTARG;;
        \?) echo "invalid option -$OPTARG" 1>&2 ; exit 1;;
         :) echo "option -$OPTARG requires an option" 1>&2; exit 1;;
    esac
done
echo opt_p=$opt_p

set -e

pushd tests
echo 'Testing system configuration before building...'
source test_prerequisites.sh
echo
popd

#PREFIX=$(readlink -f $opt_p)
#mkdir -p $PREFIX
PREFIX=$(mkdir -p $opt_p; cd $opt_p; pwd)
export PATH=$PREFIX/bin:$PATH
export PYTHONPATH=$PREFIX/lib/python2.7/site-packages:$PYTHONPATH
echo "Installing in PREFIX=$PREFIX"

cat <<EOF > setup.cfg
[build_ext]
include-dirs=$PYTHON_INCLUDE:$NUMPY_INCLUDE

EOF

$python setup.py install --prefix=$PREFIX

$python tests/ut.py

echo;
echo "Be sure to add the following to your .bashrc or equivalent:"
echo "  "PATH=$PREFIX/bin:'$PATH'
echo "  "PYTHONPATH=$PREFIX/lib/python2.7/site-packages:'$PYTHONPATH'
