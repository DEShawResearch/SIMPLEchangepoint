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


set -e
set +x

pushd $EXAMPLESDIR

HAVE_MPIEXEC=0 && which mpiexec 2>/dev/null 1>/dev/null && HAVE_MPIEXEC=1
HAVE_MPI4PY=0 && $python -c 'import mpi4py' 2>/dev/null && HAVE_MPI4PY=1

echo 'Testing serial invocation'

echo "detect_changed_distances TrpCage.mae TrpCage.dcd 'noh' --workdir=contacts --identifier=serial --analysis-mode=CONTACTS" | tee contacts_serial.log
unbuffer detect_changed_distances TrpCage.mae TrpCage.dcd 'noh' --workdir=contacts --identifier=serial --analysis-mode=CONTACTS 2>&1 | tee -a contacts_serial.log

echo "detect_changed_distances TrpCage.mae TrpCage.dcd 'name CA' --workdir=all_pairs --identifier=serial --analysis-mode='ALL' --stride 5" | tee all_pairs_serial.log
unbuffer detect_changed_distances TrpCage.mae TrpCage.dcd 'name CA' --workdir=all_pairs --identifier=serial --analysis-mode='ALL' --stride 5 2>&1 | tee -a all_pairs_serial.log


if [ $HAVE_MPIEXEC -eq "1" ]
then
    echo 'Found mpiexec'
else
    echo 'Did not find mpiexec'
fi

if [ $HAVE_MPI4PY -eq "1" ]
then
    echo 'Found mpi4py'
else
    echo 'Did not find mpi4py'
fi

if [ $HAVE_MPIEXEC -eq "1" ] && [ $HAVE_MPI4PY -eq "1" ]
then
    echo 'Testing parallel invocation'

    echo "mpiexec -n 4 detect_changed_distances TrpCage.mae TrpCage.dcd 'noh' --parallel --workdir=contacts --identifier=parallel --analysis-mode='CONTACTS' --stride 5" | tee contacts_parallel.log
    mpiexec -n 4 detect_changed_distances TrpCage.mae TrpCage.dcd 'noh' --parallel --workdir=contacts --identifier=parallel --analysis-mode='CONTACTS' --stride 5 2>&1 | tee -a contacts_parallel.log

    echo "mpiexec -n 4 detect_changed_distances TrpCage.mae TrpCage.dcd 'name CA' --parallel --workdir=all_pairs --identifier=parallel_full_trajectory --analysis-mode='ALL' --stride 1" | tee all_pairs_parallel.log
    mpiexec -n 4 detect_changed_distances TrpCage.mae TrpCage.dcd 'name CA' --parallel --workdir=all_pairs --identifier=parallel_full_trajectory --analysis-mode='ALL' --stride 1 2>&1 | tee -a all_pairs_parallel.log

else
    echo 'Not testing parallel invocation'
fi

popd
