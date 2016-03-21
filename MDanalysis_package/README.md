SIMPLE changepoint MD analysis package
======================================

A guide to the SIMultaneous Penalized Likelihood Estimate (SIMPLE) changepoint MD analysis package.

Prerequisites
-------------
* [gcc] (>= 4.6.1 and <= 4.7.2) - The de facto free compiler of choice.
* [python] (2.7) - "A programming language that lets you work quickly and integrate systems more effectively."
* [numpy] - "The fundamental package for scientific computing with Python."
* [boost.python] - "A C++ library which enables seamless interoperability between C++ and the Python programming language."
* [sqlite] - "A software library that implements a self-contained, serverless, zero-configuration, transactional SQL database engine"
* [scipy] - "A Python-based ecosystem of open-source software for mathematics, science, and engineering."
* [pytables] - A package for managing large datasets based on the HDF5 library (installed separately.)
* [lp_solve] - "A Mixed Integer Linear Programming (MILP) solver."
* [mpi4py] (optional) - Python bindings for MPI (requires a working MPI installation, such as Open MPI, MPICH 2, or LAM/MPI.)
* [vmd] (optional) - "A molecular visualization program for displaying, animating, and analyzing large biomolecular systems using 3-D graphics and built-in scripting."
* [matplotlib] (optional) - "A python 2D plotting library which produces publication quality figures in a variety of hardcopy formats and interactive environments across platforms."
* [pygtk] (optional) - "A set of Python wrappers for the GTK+ graphical user interface library."

[gcc]:https://gcc.gnu.org/
[python]:https://www.python.org/
[numpy]:http://www.numpy.org/
[boost.python]:http://www.boost.org/doc/libs/1_55_0/libs/python/doc/
[sqlite]:http://www.sqlite.org/
[scipy]:http://www.scipy.org/
[pytables]:http://www.pytables.org
[lp_solve]:http://lpsolve.sourceforge.net/5.5/
[mpi4py]:http://www.mpi4py.scipy.org
[vmd]:http://www.ks.uiuc.edu/Research/vmd/
[matplotlib]:http://matplotlib.org/
[pygtk]:http://www.pygtk.org/

Installation
------------

This package provides the full SIMPLE changepoint suite and comprises
the core package and plus one executable (`detect_changed_distances`)
and one Python module (`analyze_changed_distances`).  Apart from the
core changepoint package, these scripts depend on another Python
module (`changepoint_vmd`) and three Python extensions (`molfile`,
`periodicfix`, and `msys`) that must be compiled from source and depend on
third-party software in turn.

1) Edit `config.sh` so that the sqlite, python, boost, numpy, and
   lp_solve header files and and libraries are correct. These
   directories are distinct at DESRES; it is OK if one or more of
   these are the same on your system.  PYTHON_INCLUDE might end in
   python2.7 instead of include.

2) Run `build-all.sh`.  This script takes options:

    -j N       build N targets at a time (e.g. -j4)
    -p PREFIX  install compiled libraries to PREFIX (default .)

This script will test the configuration and run numerous unit tests
for the molfile, periodicfix, and msys extensions as well as the
changepoint software as the build progresses.  The build takes a few 
minutes running on a 2009-era processor (Intel(R) Xeon(R) W3550).

3) PATH and PYTHONPATH should include $PREFIX/bin and
   $PREFIX/lib/python respectively.  Edit your `~/.bashrc` or an
   equivalent configuration file to use this software in new
   terminals:

    PATH=$PREFIX/bin:$PATH
    PYTHONPATH=$PREFIX/lib/python:$PREFIX/lib/python2.7/site-packages:$PYTHONPATH

(You may need to use export or setenv to expose these changes.)

Usage
-----

Detailed documentation is available in the docs directory and as
Python docstrings.

Briefly, the `detect_changed_distances` script finds changepoints by
running the core algorithm on distance-based time series (note: this
script does not support any periodic wrapping, so the input trajectory
should be sanitized first, if needed).  Output is organized into
workdirs and one or more "identifiers" (workdir subdirectories).  If
an MPI implementation and the mpi4py Python module are available, this
script can be run in parallel.

    # Analyze all pairs of distances in an atomsel
    $ mpiexec -n 4 detect_changed_distances \
        TrpCage.mae TrpCage.dcd 'name CA' \
        --parallel --workdir=all_pairs --analysis-mode='ALL'

    # Analyze the pairs of atoms that get close to each other
    $ mpiexec -n 4 detect_changed_distances \
        TrpCage.mae TrpCage.dcd 'noh' \
        --parallel --workdir=contacts --analysis-mode='CONTACTS'

The `analyze_changed_distances` Python module provides handlers for the
changepoint output.  Multiple trajectories can be analyzed in the same
workdir under different identifiers and examined for common features,
such as time series that change in several trajectories.  The module
also contains software specifically designed to highlight structural
changes in VMD.  Unlike other commands, the VMDDisplay convenience
function will only work within VMD.

    # Start the embedded Python within VMD
    $ vmd
    ...
    vmd > gopython
    ...
    >>>

    # Load some common changes from big_protein_workdir/trj_0
    >>> from analyze_changed_distances import WorkdirChanges
    >>> wc = WorkdirChanges('big_protein_workdir')
    >>> cc = wc.commonResidueChangesByNumChangeTimes(100)
    >>> tc = wc.trajectoryChanges('trj_0')
    >>> trj0_changes = tc.changesByNumChangeTimes(100, residue_pairs=cc)

    # Assuming trajectory is loaded as molid 0 exactly as analyzed
    # (first and last frames and stride), use dynamic representations
    # to show show changed residues for 5 frames before and after each
    # changepoint
    >>> from analyze_changed_distances import VMDDisplay
    >>> VMDDisplay(trj0_changes, window=5, molid=0)

