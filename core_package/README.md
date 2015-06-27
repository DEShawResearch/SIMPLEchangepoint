SIMPLE changepoint core package
===============================

A guide to the SIMultaneous Penalized Likelihood Estimate (SIMPLE)
changepoint core package.

Prerequisites
-------------

* [python] - "A programming language that lets you work quickly and integrate systems more effectively."
* [numpy] - "The fundamental package for scientific computing with Python."
* [scipy] - "A Python-based ecosystem of open-source software for mathematics, science, and engineering."
* [mpi4py] (optional) - Python bindings for MPI (requires a working MPI installation, such as Open MPI, MPICH 2, or LAM/MPI.)
* [pytables] (optional) - A package for managing large datasets based on the HDF5 library (installed separately.)

[python]:https://www.python.org/
[numpy]:http://www.numpy.org/
[scipy]:http://www.scipy.org/
[mpi4py]:http://www.mpi4py.scipy.org
[pytables]:http://www.pytables.org

Installation
------------

The SIMPLE changepoint core package comprises a Python extension and a
Python script based on that extension.  To install this software,
simply run the install script to install to a path of your choice:

    $ ./install.sh -p PREFIX

where PREFIX should be replaced by the path to your preferred Python
installation directory.  Note also that it might be necessary to adjust
values set in the file config.sh depending on your local environment.

After running the installation script, be sure to update your PYTHONPATH and
PATH environment variables to include the subdirectories of PREFIX in which
the SIMPLEchangepoint library and the ComputeSIMPLEChanges script were
installed.


Usage
-----

To run SIMPLE changepoint from within a Python session:

    >>> from SIMPLEchangepoint import ComputeChanges
    >>> ComputeChanges(data, lam)

where data is a 2D numpy array or pytables (HDF5) CArray or EArray,
and lam is the lambda parameter to control the magnitude of the
penalty function.  See Python docstrings for full details.

To run from a command line:

    $ ComputeSIMPLEChanges data_file output_changes_file.pkl \
      [--lambda LAMBDA] --verbose

where data_file is either a cPickle'd 2D numpy data array or an HDF5
file (with .h5 file-name extension). See ComputeSIMPLEChanges --help
for additional details.

For large data sets, it is recommended to run in parallel mode using MPI:

    $ mpiexec -n nprocs \
      ComputeSIMPLEChanges data_file output_changes_file.pkl \
      [--lambda LAMBDA] --verbose --parallel

Example
-------

The install script should produce some simple data in the tests
directory that can be analyzed as follows:

    $ ComputeSIMPLEChanges tests/data.pkl tests/data.lam_32.pkl \
      --lambda 32 --verbose

    # Generated only if PyTables was found
    $ ComputeSIMPLEChanges tests/data.h5 tests/data.lam_32.pkl \
      --lambda 32 --verbose

