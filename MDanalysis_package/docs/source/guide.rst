Introduction
=======================================
The SIMPLE_MDanalysis package provides tools to perform event detection and
changepoint analysis for molecular dynamics trajectories by detecting changes
in pairwise distance measurements between user-selected atoms. It provides a
module to analyze these changes in Python and to visualize the detected changes 
in VMD. A mode of analysis is provided to use this workflow to detect and
visually highlight important changes in chemical contacts between protein 
residues.

This package is built around the SIMPLEchangepoint library, which must be
separately installed as a prerequisite. The package also requires an
installation of HDF5 and the pytables Python module, as well as numpy, scipy,
and matplotlib. An (optional) installation of MPI and mpi4py is required for
parallel processing, and an (optional) installation of VMD with the Python
interpreter is required for visualization.

``detect_changed_distances``
==================================================================
The ``detect_changed_distances`` executable computes distances between
selected pairs of atoms in a trajectory and finds changepoints in
them.  The changepoints can be subsequently analyzed or visualized
using the ``analyze_changed_distances`` Python module (see below.) For
correct behavior of these tools, the input system should be annotated
such that each atom in the system is uniquely identified by a
combination of chain name, residue name, resid, and atom name.

Modes of analysis
""""""""""""""""""""""""""""""""""""""""""
Two distinct modes of analysis are available and are selected by the
*analysis-mode* option:

    Under the default option 'ALL', all pairwise distances are
    analyzed. For this mode, it is recommended that *atomsel-A* and
    *atomsel-B* select one atom per residue; these can be alpha carbons
    or a single representative sidechain atom per residue for
    proteins. This mode of analysis is designed to summarize
    large-scale structural changes in proteins such as fast-folding
    protein domains and BPTI. Example::

    $ mpiexec -n 4 detect_changed_distances small_protein.mae small_protein.dcd 'name CA' --parallel --workdir=all_pairs --analysis-mode='ALL'

    Under analysis-mode 'CONTACTS', only pairs of atoms from distinct
    residues that come within 4 Angstroms during the trajectory are
    analyzed. It is recommended that the user select all (or a
    representative few) heavy atoms per residue of interest in
    *atomsel-A* and *atomsel-B*.  This mode of analysis is designed to
    identify important changes in sidechain contacts.  Note: a
    sigmoid-type transform is applied to the distance measurements to
    highlight changes around 4 Angstroms.  Example::

    $ mpiexec -n 4 detect_changed_distances large_protein.mae large_protein.dcd 'noh' --parallel --workdir=contacts --analysis-mode='CONTACTS'

Organizing analysis
"""""""""""""""""""""""""""""""
Changepoint analysis is written to a directory *workdir*, which should
be placed on a filesystem with high storage capacity. Analyses for
related trajectories, e.g. of the same or similar chemical systems,
may be placed in the same workdir. Within a workdir, analyses are
identified by their *identifier* labels. Once used, an identifier
label corresponds to certain arguments, including the trajectory,
frame selection, atom selections, and mode of analysis.  These
parameters must be specified for the first run of this program with a
new identifier, during which they and the computed distance time
series are saved to disk.  Subsequent runs with the same workdir and
identifier but with new lambdas (see below) are allowed, but they will
reuse these stored data preferentially.

Specifying sensitivity
"""""""""""""""""""""""""""""""
The sensitivity of the analysis is controlled by a parameter
:math:`\lambda` in the changepoint algorithm. Smaller values of
:math:`\lambda` will result in more detected changes.  The time-scale
of detected changes is undefined, but for a given set of time series
is proportional to :math:`\lambda`.  As the exact relationship between
:math:`\lambda` and the time-scale of detected changes is difficult to
determine a priori, it is suggested that the user run the analysis
over a decreasing range of :math:`\lambda` values to determine which
value best corresponds to the desired time-scale of analysis. To
facilitate this process, the starting value of :math:`\lambda` is
specified by *lambda-start*, and optional *max-change-times* and
*lambda-scale* arguments may be provided so that the changepoint
analysis is run repeatedly, increasing the number of detected changes
for each subsequent run by multiplying the previous :math:`\lambda`
value by *lambda-scale* and terminating when at least
*max-change-times* total change times are detected.  As a conservative
starting point, *lambda-start* defaults to the power of 2 just larger
than :math:`J \log_2(T)^2/1000`, where :math:`J` and :math:`T` are the
number of time series and frames respectively.


Specifying the trajectory, atoms, and frames
""""""""""""""""""""""""""""""""""""""""""""""""
For the first run of ``detect_changed_distances`` with a new *identifier* label,
the system and trajectory are specified by the *structure-file* and
*trajectory-file* options. The structure file may be in any format recognized by
the MSYS library (including MAE, DMS, and PDB), and the corresponding trajectory
file must be in DCD or DTR/STK format. *first-frame*, *last-frame*, and *stride*
options may be specified to select a subset of frames for analysis, although for
reasons of performance and memory usage, DCD files should ideally be
pre-strided. Atomic coordinates should be appropriately unwrapped for 
simulations with periodic boundary conditions. The set of atoms to be analyzed
is specified by the *atomsel-A* and *atomsel-B* options, where atom selections
should be given in the VMD atom selection language. If both *atomsel-A* and
*atomsel-B* are provided, distances are taken between pairs of one atom from
each selection. Otherwise, distances are taken between pairs of atoms in
*atomsel-A*. With :math:`J` distance measurements and :math:`T` frames, the 
runtime of the algorithm is roughly :math:`O(JT\log T)`. For reasonable
performance, the total number of selected frames should not exceed ~100000 for 
an analysis with a small number (~500) of distance time series or ~10000 for an
analysis with a large number (~10000) of distance time series.


Fine-tuning penalty and handling symmetric atoms
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
The remaining options control detailed behavior of the method. The
*atom-groups-file*, *alpha*, and *beta* options control the shape of the penalty
function used in SIMPLEchangepoint; see documentation there for details. (Groups
of time series observables corresponding to atom pairs are taken to be the set 
products of pairs of groups of atoms specified by *atom-groups-file*.) These 
options take default values depending on the mode of analysis and in general do 
not need to be set by the user unless fine-tuning is desired. By default, 
symmetric atoms within a residue are treated as a single atom; the
*include-symmetric-atoms* flag may be specified to treat them instead as
distinct atoms.

Usage
"""""""""""""""""""""""""""""""

.. program:: detect_changed_distances

.. describe:: detect_changed_distances structure_file trajectory_file atomsel_A [ options ]

Positional arguments:

.. cmdoption::  structure_file

   Input structure file (mae or dms)

.. cmdoption::  trajectory_file 

   Input trajectory file (stk or dcd)

.. cmdoption::  atomsel_A

   Selection to analyze (msys atomsel)


Options:

.. cmdoption::  --analysis-mode ANALYSIS_MODE

   Specify 'ALL' or 'CONTACTS' [default: 'ALL'].

.. cmdoption::  --workdir WORKDIR

   Directory to store output [default: changepoint].

.. cmdoption::  --identifier IDENTIFIER

   String identifier for current analysis [default: lowest unused natural number].

.. cmdoption::  --lambda-start LAMBDA_START

   Starting value for lambda, the sensitivity parameter; lower is more sensitive [default: power of 2 just above :math:`J \log_2(T)^2/1000`].

.. cmdoption::  --lambda-scale LAMBDA_SCALE

   Repeat analysis scaling lambda by this factor each time [default: 0.5].

.. cmdoption::  --max-change-times MAX_CHANGE_TIMES

   Repeat analysis with decreasing lambdas until at least this many change times are detected [default: 0 (don't repeat)].

.. cmdoption::  --first-frame FIRST_FRAME

   First frame to analyze [default: 0, beginning].

.. cmdoption::  --last-frame LAST_FRAME

   Last frame to analyze [default: last frame].

.. cmdoption::  --stride STRIDE

   Stride length in number of frames [default: select about 1000 total frames].

.. cmdoption::  --atomsel-B ATOMSEL_B

   Second atom selection; if given, analyze pairs from the direct product atomsel_A x atomsel_B [default: None]

.. cmdoption::  --include-symmetric-atoms

   Do not reduce groups of distances based on symmetry-related atoms (e.g. methyl hydrogens) into single time series [default: use minimum distance].

.. cmdoption::  --atom-groups-file ATOM_GROUPS_FILE

   Atom grouping specification as a cPickled list of atom ID lists [default: group by five surrounding residues]

.. cmdoption::  --beta BETA

   Beta (within-group exponent) parameter [default: 0.7].

.. cmdoption::  --alpha ALPHA

   Alpha (between-group exponent) parameter [default: 0.99 if --analysis-mode=CONTACTS or 0.7 if --analysis-mode=ALL]


``analyze_changed_distances``
=================================================
The ``analyze_changed_distances`` Python module provides utility classes and
functions to load the output from the ``detect_changed_distances`` executable
and, if imported inside a VMD session, to visualize the changes in VMD. For
correct behavior, the structure file input to ``detect_changed_distances``
should be annotated such that atoms are uniquely specified by the combination of
chain name, residue name, resid, and atom name.

Accessing changes
""""""""""""""""""""""""""""""""""""""""""""""""
The following loads all changes output by ``detect_changed_distances`` for a 
single *workdir*, accesses changes for a single *identifier* from that workdir,
and accesses changes corresponding to a single run of the SIMPLEchangepoint 
algorithm at a :math:`\lambda=20` sensitivity level::

    >>> from analyze_changed_distances import WorkdirChanges
    >>> wkdir_changes = WorkdirChanges('SIMPLE_wkdir')
    >>> trj_changes = wkdir_changes.trajectoryChanges('trj0')
    >>> changes_20 = trj_changes.changes(20)

Changes for a single *identifier* may also be loaded separately::

    >>> from analyze_changed_distances import TrajectoryChanges
    >>> trj_changes = TrajectoryChanges('SIMPLE_wkdir', 'trj0')
    >>> changes_20 = trj_changes.changes(20)

The following is a typical example of the format for changes accessed in this
way (with output snipped for brevity)::

    >>> changes_20
    {431280.0: set([('(A)TRP-109:CH2', '(C)BIA-1:CAA'),
          ('(A)TRP-109:CE3', '(C)BIA-1:CAA'),
          ('(A)TRP-109:CZ3', '(C)BIA-1:CAA')]),
     483840.0: set([('(A)PHE-223:CE1/CE2', '(A)GLU-268:O')]),
     556740.0: set([('(A)VAL-24:O', '(A)ARG-28:CB'),
          ('(A)VAL-24:O', '(A)ARG-28:CA'),
          ('(A)VAL-24:O', '(A)ARG-28:N')]),
     ...
     1339380.0: set([('(A)TRP-99:CH2', '(A)TRP-105:CD1'),
          ('(A)PHE-89:CG', '(A)TRP-105:NE1'),
          ('(A)PHE-89:CD1/CD2', '(A)TRP-105:NE1'),
          ('(A)PHE-89:CD1/CD2', '(A)TRP-105:CD1'),
          ('(A)TRP-99:CZ2', '(A)TRP-105:CD1'),
          ('(A)PHE-89:CZ', '(A)TRP-105:NE1'),
          ('(A)PHE-89:CE1/CE2', '(A)TRP-105:NE1')])}

Each numeric key of this dictionary corresponds to a single change time
:math:`t` (in ps) where the distances between the pairs of atoms in the
associated set value were determined to have changed between frames of time
:math:`<t` and frames of time :math:`\geq t`. Pairs of atoms are specified by a
pair of strings indicating the chain name, residue name, resid, and atom name of
each atom. As the ``detect_changed_distances`` analysis combines symmetric atoms
into a single atom by default, a string such as '(A)PHE-223:CE1/CE2' represents
the combination of two symmetric 'CE' atoms of this residue.

In a contact-detection analysis, there may be many pairs of changed atoms for 
each pair of residues. A convenience function is provided to summarize a
dictionary of atom-pair changes into one of residue-pair changes::

    >>> from analyze_changed_distances import ChangesToResidueChanges
    >>> ChangesToResidueChanges(changes_20)
    {431280.0: set([('(A)TRP-109', '(C)BIA-1')]),
     483840.0: set([('(A)PHE-223', '(A)GLU-268')]),
     556740.0: set([('(A)VAL-24', '(A)ARG-28')]),
     ...
     1339380.0: set([('(A)PHE-89', '(A)TRP-105'), ('(A)TRP-99', '(A)TRP-105')])}

Options are provided to only access changes corresponding to specific atom
selections, pairs of atoms, or pairs of residues. For example, all changes
between pairs of one heavy atom from 'chain A' and a second heavy atom from
'chain B', or between atoms in a specific list of atom or residue pairs, may be
accessed as follows::

    >>> changes_20_AB = trj_changes.changes(20, selection_pair=('chain A and noh', 'chain B and noh'))
    >>> changes_20_specific_atoms = trj_changes.changes(20, atom_pairs=[('(A)TRP-109:CH2', '(C)BIA-1:CAA'), ('(A)PHE-223:CE1/CE2', '(A)GLU-268:O')])
    >>> changes_20_specific_residues = trj_changes.changes(20, residue_pairs=[('(A)TRP-109', '(C)BIA-1'), ('(A)PHE-223', '(A)GLU-268')])

The input format for lists of atom pairs and residue pairs matches the output
format of :meth:`TrajectoryChanges.changes`,
:meth:`WorkdirChanges.commonChanges`, and
:meth:`WorkdirChanges.commonResidueChanges` to provide an easy way filter the 
changes for this *identifier* using changes of another *identifier*.

The :meth:`TrajectoryChanges.changes` method accesses changes for a given 
:math:`\lambda` sensitivity. Convenience methods
:meth:`TrajectoryChanges.changesByNumChangeTimes` and 
:meth:`TrajectoryChanges.changesByNumChanges` are provided to instead 
automatically select the :math:`\lambda` sensitivity (among those loaded for
this *identifier*) that detected a number of changes closest to the given number
of total change times or total observable changes. (The number of total change 
times is the number of keys of the returned dictionary; the number of total 
observable changes is the sum of the sizes of all the values of the returned
dictionary.)

Plotting changes
""""""""""""""""""""""""""""""""""""""""""""
Two methods are provided to visualize changes using :class:`matplotlib`. The
following plots the distance measurements for a single pair of atoms over time,
along with all changes detected for this pair of atoms at a particular
sensitivity level::

    >>> from analyze_changed_distances import TrajectoryChanges
    >>> trj_changes = TrajectoryChanges('SIMPLE_wkdir', 'trj0')
    >>> trj_changes.plotDistance(('(A)ARG-131:CZ', '(A)GLU-268:OE1/OE2'), lam=20)

The following plots all changed atom pairs at a single change time as a matrix
plot, with atoms in *atomsel_A* on one axis and atoms in *atomsel_B* on the
other axis::

    >>> changes = trj_changes.changes(20)
    >>> trj_changes.matrixPlotChange(changes[431280.0], lam=20)

Clicking on a square in this matrix plot will call
:meth:`TrajectoryChanges.plotDistance` for the pair of atoms associated with 
that square, if these distances were computed by ``detect_changed_distances``,
and the optional *lam* argument is passed to this call.

Comparing changes across trajectories
""""""""""""""""""""""""""""""""""""""""""""
If a *workdir* contains analyses from multiple related trajectories (e.g. of the
same or similar chemical systems), convenience methods are provided in the 
:class:`WorkdirChanges` class to find common changes detected across these
trajectories. The :meth:`WorkdirChanges.commonChanges`,
:meth:`WorkdirChanges.commonChangesByNumChangeTimes`,
and :meth:`WorkdirChanges.commonChangesByNumChanges` methods run the
corresponding :class:`TrajectoryChanges` method for all or a specified list of
*identifiers* in the *workdir* and return the set of atom pairs that were
detected to change in at least a given number of these *identifiers*. For
instance, the following loads all changes in a *workdir*, selects the changes
between 'chain A' and 'chain B' in each of the trajectories 'trj0', ..., 'trj5'
for a :math:`\lambda` sensitivity level returning close to 100 such change times
per trajectory, and determines pairs of atoms that changed in at least 4 of
these 6 trajectories::

    >>> from analyze_changed_distances import WorkdirChanges
    >>> wkdir_changes = WorkdirChanges('SIMPLE_wkdir')
    >>> wkdir_changes.commonChangesByNumChangeTimes(100, selection_pair=('chain A', 'chain B'), at_least=4, identifiers=['trj0', 'trj1', 'trj2', 'trj3', 'trj4', 'trj5'])
    set([('(A)ARG-131:CZ', '(B)GLU-268:OE1/OE2'),
         ('(A)TYR-219:CZ', '(B)GLY-276:N'),
         ('(A)ARG-131:NE', '(B)GLU-268:OE1/OE2'),
         ('(A)TYR-219:OH', '(B)LEU-272:CD1/CD2'),
         ...
         ('(A)TYR-326:O', '(B)SER-329:O'),
         ('(A)ALA-128:N', '(B)LEU-275:CD1/CD2'),
         ('(A)ILE-127:CG2', '(B)LEU-275:CD1/CD2')])


To obtain common pairs of residues containing changes in a group of
trajectories, the :meth:`WorkdirChanges.commonResidueChanges`, 
:meth:`WorkdirChanges.commonResidueChangesByNumChangeTimes`, and
:meth:`WorkdirChanges.commonResidueChangesByNumChanges` methods may be used 
instead::

    >>> wkdir_changes.commonResidueChangesByNumChangeTimes(100, selection_pair=('chain A', 'chain B'), at_least=4, identifiers=['trj0', 'trj1', 'trj2', 'trj3', 'trj4', 'trj5'])
    set([('(A)ARG-131', '(B)GLU-268'),
         ('(A)TYR-219', '(B)GLY-276'),
         ('(A)TYR-219', '(B)LEU-272'),
         ...
         ('(A)TYR-326', '(B)SER-329'),
         ('(A)ALA-128', '(B)LEU-275'),
         ('(A)ILE-127', '(B)LEU-275')])

Note that there is a difference between using
:meth:`WorkdirChanges.commonResidueChanges` and using
:meth:`WorkdirChanges.commonChanges` followed by the
:meth:`ChangesToResidueChanges` convenience function. In the 
first approach, atom-pair changes for each trajectory are mapped to residue-pair
changes, and then residue-pair changes across trajectories are compared. In the
second approach, atom-pair changes are compared across trajectories, and then
the common changed atom-pairs are mapped to residue-pairs.

In comparing changes across trajectories, atoms and residues are identified by
their chain names, residue names, resids, and atom names. Trajectories being 
compared do not need to have identical chemical systems, provided that the
naming of common residues and atoms are consistent.

Visualizing changes in VMD
""""""""""""""""""""""""""""""""""""""""""""
The ``analyze_changed_distances`` module may be loaded inside a VMD session to 
dynamically display the detected changes as you scroll through the trajectory in
VMD. For this to have the correct behavior, frame 0 in VMD must correspond to
the structure file (DMS, MAE, PDB, ...) and the remaining frames 1,...,n loaded
in VMD must correspond exactly to the frames specified by the *first-frame*, 
*last-frame*, and *stride* inputs to ``detect_changed_distances`` (which is all
frames of the DCD or DTR/STK file if these inputs were not specified). Supposing
that you are in a VMD session in which the appropriate frames of 'trj0' of a
*workdir* have been loaded, the following will determine some residue changes
common to all trajectories in this *workdir*, access these common changes in
'trj0', and display them in VMD::

    >>> from analyze_changed_distances import WorkdirChanges, VMDDisplay
    >>> wkdir_changes = WorkdirChanges('SIMPLE_wkdir')
    >>> common_changes = wkdir_changes.commonResidueChangesByNumChangeTimes(100)
    >>> trj0_changes = wkdir_changes.trajectoryChanges('trj0').changesByNumChangeTimes(100, residue_pairs=common_changes)
    >>> VMDDisplay(trj0_changes, window=5, molid=0)

The :func:`VMDDisplay` function displays each change time :math:`t` for *window*
currently loaded frames before and after :math:`t`. Residues containing atoms 
that change at :math:`t` are shown using a gray licorice representation in these
frames and become colored (by element) in the two frames immediately preceding 
and following :math:`t`.

Bond labels may be used in the frames immediately preceding and following
:math:`t` to indicate the specific pairs of atoms whose distances change. To
enable this feature, :func:`VMDDisplay` should be passed a *label_before_after*
function argument that controls which bond labels are displayed. This
*label_before_after* function takes as input the median of the distance of an 
atom pair in the *window* before the change, the median of this distance in the
*window* after the change, as well as the IDs of the atoms in the pair and
outputs whether to display the bond label before the change and after the change
as a pair of boolean values. The arguments to the *label_before_after* function
may be used to selectively display bond labels corresponding to certain types of
changed distances. The following example displays bond labels if the median 
distance changes between a value less than 10 Angstroms and a value greater than
10 Angstroms::

    >>> def label_before_after(median_before, median_after, aid0, aid1):
    ...     label_before = (median_before < 10 and median_after > 10)
    ...     label_after = (median_after < 10 and median_before > 10)
    ...     return label_before, label_after
    ...     
    >>> VMDDisplay(trj0_changes, window=5, molid=0, label_before_after=label_before_after)

In addition to displaying the change in VMD, :func:`VMDDisplay` will also open a
:class:`matplotlib` window with the horizontal axis indexed by frame, red dots
indicating the times of changes, and a dynamically-updated vertical bar
indicating the currently displayed frame. The user may provide an auxiliary time
series, e.g. all-atom RMSD, specified by the *observable* argument to
:func:`VMDDisplay`, to also plot in this window.

As changes are specified to :func:`VMDDisplay` based on chain name, residue
name, resid, and atom name, the VMD session does not need to have all atoms of
the system loaded, but it must have loaded all atoms involved in any of the
changes to be displayed. The :class:`matplotlib` window and dynamic molreps 
created by :func:`VMDDisplay` cannot be closed/deleted manually---they can be 
removed by the :func:`analyze_changed_distances.VMDClear` function or replaced
by a second call to :func:`VMDDisplay`. Only one set of changes may be displayed
in VMD at a time.
