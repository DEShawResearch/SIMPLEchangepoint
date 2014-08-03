# This software has been built and tested with Python 2.7.3 and numpy
# 1.6.2 using GCC 4.7.2.

# Set to the name of the python executable
if [ -z "$python" ]
then
    python=python2.7
fi

# Provide C/C++ header files - <Python.h>  <numpy/ndarrayobject.h>
# These should work automatically.
PYTHON_INCLUDE=`$python -c 'from distutils.sysconfig import get_python_inc; print get_python_inc()'`
NUMPY_INCLUDE=`$python -c 'import numpy; print numpy.get_include()'`

# Name of the Python executable
python=python2.7
