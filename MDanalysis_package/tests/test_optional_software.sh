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

echo 'Searching for optional software'
HAVE_OPTIONAL=1

HAVE_MATPLOTLIB=0 && \
    $python -c 'import matplotlib' 2>/dev/null 1>/dev/null && \
    HAVE_MATPLOTLIB=1

HAVE_PYGTK=0 && \
    $python -c 'import gtk' 2>/dev/null 1>/dev/null && \
    HAVE_PYGTK=1

HAVE_VMD=0 && \
    which vmd 2>/dev/null 1>/dev/null && \
    HAVE_VMD=1

if [ $HAVE_MATPLOTLIB -eq "1" ]
then
    echo "Found matplotlib"
else
    echo "Couldn't find matplotlib"
    HAVE_OPTIONAL=0
fi

if [ $HAVE_PYGTK -eq "1" ]
then
    echo "Found pygtk"
else
    echo "Couldn't find pygtk"
    HAVE_OPTIONAL=0
fi

if [ $HAVE_VMD -eq "1" ]
then
    echo "Found vmd"
else
    echo "Couldnt' find vmd"
    HAVE_OPTIONAL=0
fi

if [ $HAVE_OPTIONAL -eq "1" ]
then
    echo "OK:      found all optional software."
else
    echo "WARNING: some optional software was not found; VMD-based "
    echo "         visualization will not be available."
fi
