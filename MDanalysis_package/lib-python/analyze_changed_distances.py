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
"""
This module may be loaded inside a VMD session to dynamically display
the detected changes as you scroll through the trajectory in VMD. For
this to have the correct behavior, frame 0 in VMD must correspond to
the structure file (DMS, MAE, PDB, ...) and the remaining frames
1,...,n loaded in VMD must correspond exactly to the frames specified
by the first-frame, last-frame, and stride inputs to
detect_changed_distances (which is all frames of the DCD or DTR/STK
file if these inputs were not specified).
"""
import numpy as np
import cPickle
from collections import defaultdict
import os
import tables
import msys
import re
import sys
try:
    import matplotlib
    matplotlib.use('GTKAgg')
    import matplotlib.pyplot as plt
except RuntimeError:
    print 'WARNING: matplotlib import failed'
    pass
if 'vmd' in sys.modules:
    import vmdcallbacks
    import gtk
    vmdcallbacks.add_callback('display_update',
            lambda: gtk.main_iteration(block=False))

class TrajectoryChanges(object):
    """Convenience class to analyze output of detect_changed_distances tool.

    Loads output of detect_changed_distances for all settings of the lambda
    sensitivity parameter for a single identifier label. Provides functions to
    select changes involving a sub-selection of atoms, visualize the set of
    changed observables at a single time as a matrix plot, and plot a single
    distance observable with changes for that distance.
    """

    def __init__(self, workdir, identifier):
        """Load changes from detect_changed_distances for a single identifier.

        Arguments:
            workdir -- str
            identifier -- str

        """
        path = os.path.join(workdir, identifier)
        file = open(os.path.join(path, 'data_info.pkl'), 'r')
        self._info = cPickle.load(file)
        file.close()
        self._h5 = tables.openFile(os.path.join(path, 'data.h5'), 'r')
        self._system = msys.Load(self._info['structure_file'])
        self._changes = {}
        for f in os.listdir(path):
            if f[-4:] == '.chg':
                lam = float(f[:-4])
                file = open(os.path.join(path, f), 'r')
                self._changes[lam] = cPickle.load(file)
                file.close()

    @property
    def system(self):
        """Handle to the msys.System object for this identifier."""
        return self._system

    @property
    def lambdas(self):
        """List of all lambda sensitivity parameters run for this identifier."""
        return sorted(self._changes.keys())

    def _ids_to_info(self, ids):
        atom = self._system.atom(ids[0])
        atom_name = atom.name
        for a in ids[1:]:
            atom_name += '/' + self._system.atom(a).name
        return '(%s)%s-%d:%s' % (atom.residue.chain.name,
                atom.residue.name, atom.residue.resid, atom_name)

    def _info_to_ids(self, info):
        pattern = re.compile(r"^\((?P<chain>[^()]*)\)(?P<resname>.+)-(?P<resid>\d+):(?P<atomname>[^:]+)$")
        match = pattern.match(info)
        if match is None:
            raise RuntimeError, "Misformatted info string: '%s'" % info
        ids = []
        for name in match.group('atomname').split('/'):
            sel_str = 'chain %s and resname %s and resid %d and name %s' % (
                    match.group('chain'), match.group('resname'),
                    int(match.group('resid')), name)
            sel = self._system.select(sel_str)
            if len(sel) == 0:
                raise RuntimeError, \
                        "Selection '%s' does not specify a valid atom" % sel_str
            elif len(sel) > 1:
                print >> sys.stderr, \
                        "WARNING: Selection '%s' specifies more than one atom" \
                        % sel_str
            ids.append(sel[0].id)
        return tuple(sorted(ids))

    def changes(self, lam, selection_pair=None, atom_pairs=None,
            residue_pairs=None):
        """Retrieve changes for a given lambda sensitivity.

        A frame key of t in the returned dictionary indicates that there is a
        change between frames < t and frames >= t; the corresponding value in
        the dictionary gives the pairs of atoms for which their distance changed
        at this time.
        
        Three methods are provided to retrieve only a subset of changes. In the
        first, a pair of atom selection strings may be provided; a change for
        the time series of a pair of atoms is returned if and only if one atom
        belongs to each selection. In the second and third methods, a list of
        atom pairs or residue pairs may be provided; only changes corresponding
        to these specific atom pairs or residue pairs will be returned. This
        may be used to filter the changes for this trajectory using changes from
        a different trajectory or common changes from a group of trajectories.
        If none of selection_pair, atom_pairs, and residue_pairs are specified,
        all changes at this lambda sensitivity level are returned.

        Arguments:
            lam -- float, must be in the list of loaded lambda values

            selection_pair -- (str, str), where each str must be a valid atomsel

            atom_pairs -- [('(chain)residue:atom', '(chain)residue:atom'), ...]

            residue_pairs -- [('(chain)residue', '(chain)residue'), ...]

        Returns:
            { frame: set( ('(chain)residue:atom', '(chain)residue:atom'), ...)
                , ...
                }

        """
        if lam not in self._changes:
            raise RuntimeError, 'Invalid lambda value ' + str(lam)
        if selection_pair is not None:
            atoms_A = np.zeros(self._system._ptr.maxAtomId(), dtype='bool')
            tmp = self._system.select(selection_pair[0])
            for a in tmp:
                atoms_A[a.id] = True
            atoms_B = np.zeros(self._system._ptr.maxAtomId(), dtype='bool')
            tmp = self._system.select(selection_pair[1])
            for a in tmp:
                atoms_B[a.id] = True
        if atom_pairs is not None:
            atom_pairs_set = set(atom_pairs)
        if residue_pairs is not None:
            residue_pairs_set = set(residue_pairs)
        filtered_changes = defaultdict(set)
        for t in self._changes[lam]:
            for p in self._changes[lam][t]:
                info_p = (self._ids_to_info(p[0]), self._ids_to_info(p[1]))
                if atom_pairs is not None:
                    if info_p in atom_pairs_set or (info_p[1],
                            info_p[0]) in atom_pairs_set:
                        filtered_changes[t].add(info_p)
                if residue_pairs is not None:
                    residue_p = (info_p[0][:info_p[0].rfind(':')],
                            info_p[1][:info_p[1].rfind(':')])
                    if residue_p in residue_pairs_set or (residue_p[1],
                            residue_p[0]) in residue_pairs_set:
                        filtered_changes[t].add(info_p)
                if selection_pair is not None:
                    if sum(atoms_A[list(p[0])]) * \
                            sum(atoms_B[list(p[1])]) > 0 or \
                            sum(atoms_A[list(p[1])]) * \
                            sum(atoms_B[list(p[0])]) > 0:
                        filtered_changes[t].add(info_p)
                if atom_pairs is None and residue_pairs is None and \
                        selection_pair is None:
                    filtered_changes[t].add(info_p)
        return dict(filtered_changes)

    def changesByNumChangeTimes(self, num_change_times, selection_pair=None,
            atom_pairs=None, residue_pairs=None):
        """Retrieve changes by the number of total change times.

        Retrieves changes for the lambda sensitivity value such that the
        returned change list has as close to num_change_times total change
        times as possible. See docstring for 'changes' function for additional
        details.
        """
        closest_changes = None
        for lam in self._changes:
            tmp = self.changes(lam, selection_pair, atom_pairs, residue_pairs)
            if closest_changes is None or abs(num_change_times
                    - len(closest_changes)) > abs(num_change_times - len(tmp)):
                closest_changes = tmp
        return closest_changes

    def changesByNumChanges(self, num_changes, selection_pair=None,
            atom_pairs=None, residue_pairs=None):
        """Retrieve changes by the number of total changes.

        Retrieves changes for the lambda sensitivity value such that the
        returned change list has as close to num_changes total changes as
        possible. See docstring for 'changes' function for additional details.
        """
        closest_changes = None
        for lam in self._changes:
            tmp = self.changes(lam, selection_pair, atom_pairs, residue_pairs)
            count = sum([len(v) for k,v in tmp.items()])
            if closest_changes is None or abs(num_changes
                    - closest_count) > abs(num_changes - count):
                closest_changes = tmp
                closest_count = count
        return closest_changes

    def plotDistance(self, changed_pair, lam=None):
        """Plot a single distance time series with detected change points.

        Given atom pair must correspond to a pair used in the
        'detect_changed_distances' analysis. Change points for this time series
        at sensitivity level lam are plotted if lam is provided.

        Arguments:
            changed_pair -- ('(chain)residue:atom', '(chain)residue:atom')

            lam -- float

        """
        if lam is not None and lam not in self._changes:
            raise RuntimeError, 'Invalid lambda value ' + str(lam)
        a0 = self._info_to_ids(changed_pair[0])
        a1 = self._info_to_ids(changed_pair[1])
        if (a0, a1) in self._info['pair_to_index']:
            idx = self._info['pair_to_index'][(a0, a1)]
        elif (a1, a0) in self._info['pair_to_index']:
            idx = self._info['pair_to_index'][(a1, a0)]
        else:
            raise RuntimeError, 'Time series not found for pair ' \
                    + str(changed_pair)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        dists = self._h5.root.data[idx]
        if self._info['contact_dist'] > 0:
            np.random.seed(idx)
            dists -= np.random.uniform(0.0,0.1,size=(1,len(dists)))
            dists = self._info['contact_dist'] / (1.0 / dists - 1) ** 0.2
        ax.plot(self._info['frame_inds'], dists, '.')
        if lam is not None:
            times = [t for t in self._changes[lam]
                    if ((a0,a1)) in self._changes[lam][t] or \
                            ((a1,a0)) in self._changes[lam][t]]
            ax.plot(times, np.median(dists) * np.ones(len(times)), 'ro')
        ax.xaxis.set_label_text('Frame')
        ax.yaxis.set_label_text('Distance (A) between atoms %s and %s' % (changed_pair[0], changed_pair[1]))
        fig.show()

    def matrixPlotChange(self, change, lam=None):
        """Matrix plot a set of changed pairs at a single change time.

        Clicking on a square in the plot will call plotDistance for the
        corresponding pair of atoms, with the optional lam parameter passed to
        plotDistance to display changes for this distance measurement at this
        lambda sensitivity level.

        Arguments:
            change -- set( ('(chain)residue:atom', '(chain)residue:atom'), ... )

            lam -- float

        """
        if lam is not None and lam not in self._changes:
            raise RuntimeError, 'Invalid lambda value ' + str(lam)
        atoms_A = [self._info['symmetric_atoms'][a.id] for a in
            self._system.select(self._info['atomsel_A'])]
        def list_unique_in_order(atoms):
            l = []
            s = set()
            for a in atoms:
                if not a in s:
                    l.append(a)
                s.add(a)
            return l
        atoms_A = list_unique_in_order(atoms_A)
        atoms_A_labels = [self._ids_to_info(a) for a in atoms_A]
        if self._info['atomsel_B'] is None:
            atoms_B = atoms_A
            atoms_B_labels = atoms_A_labels
        else:
            atoms_B = [self._info['symmetric_atoms'][a.id] for a in
                self._system.select(self._info['atomsel_B'])]
            atoms_B = list_unique_in_order(atoms_B)
            atoms_B_labels = [self._ids_to_info(a) for a in atoms_B]
        atoms_A_dict = {}
        for i, a in enumerate(atoms_A):
            atoms_A_dict[a] = i
        atoms_B_dict = {}
        for i, a in enumerate(atoms_B):
            atoms_B_dict[a] = i
        changes_mat = np.zeros((len(atoms_A), len(atoms_B)))
        for changed_pair in change:
            found = False
            a0 = self._info_to_ids(changed_pair[0])
            a1 = self._info_to_ids(changed_pair[1])
            if a0 in atoms_A_dict and a1 in atoms_B_dict:
                changes_mat[atoms_A_dict[a0], atoms_B_dict[a1]] = 1
            if a1 in atoms_A_dict and a0 in atoms_B_dict:
                changes_mat[atoms_A_dict[a1], atoms_B_dict[a0]] = 1
            else:
                raise RuntimeError, 'Time series not found for pair ' \
                        + str(changed_pair)
        fig = plt.figure()
        fig.subplots_adjust(bottom=0.2)
        ax = fig.add_subplot(111)
        ax.imshow(changes_mat, origin='lower', interpolation='nearest', aspect='equal')
        if len(atoms_A) > 50:
            A_tick_pos = np.arange(0, len(atoms_A), len(atoms_A) * 0.02).astype(int)
        else:
            A_tick_pos = np.arange(0, len(atoms_A)).astype(int)
        if len(atoms_B) > 50:
            B_tick_pos = np.arange(0, len(atoms_B), len(atoms_B) * 0.02).astype(int)
        else:
            B_tick_pos = np.arange(0, len(atoms_B)).astype(int)
        def label_xtick(x, pos):
            x = int(round(x))
            if x < 0 or x >= len(atoms_A):
                return ''
            else:
                return atoms_A_labels[x]
        def label_ytick(y, pos):
            y = int(round(y))
            if y < 0 or y >= len(atoms_B):
                return ''
            else:
                return atoms_B_labels[y]
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=30, integer=True))
        labels = ax.xaxis.get_ticklabels()
        for label in labels:
            label.set_rotation(90)
            label.set_fontsize('small')
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(label_xtick))
        ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=30, integer=True))
        labels = ax.yaxis.get_ticklabels()
        for label in labels:
            label.set_fontsize('small')
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(label_ytick))
        ax.format_coord = lambda x,y: 'x=%s, y=%s' % (label_xtick(x, None), label_ytick(y, None))
        def click_event(event):
            if fig.canvas.toolbar.mode == '' and ax == event.inaxes and event.button == 1:
                x = label_xtick(event.xdata, None)
                y = label_ytick(event.ydata, None)
                if x == '' or y == '':
                    return
                try:
                    self.plotDistance((x,y), lam)
                except RuntimeError:
                    pass
                else:
                    return
                try:
                    self.plotDistance((y,x), lam)
                except RuntimeError:
                    pass
                else:
                    return
        fig.canvas.mpl_connect('button_press_event', click_event)
        fig.show()

class WorkdirChanges(object):
    """Convenience class to analyze output of detect_changed_distances tool.

    Loads output of detect_changed_distances for all identifier labels in a
    workdir. Provides functions to select common changed pairs detected across
    many of these identifier labels. The intended use case is where the
    identifier labels correspond to different simulations of the same or
    similar systems; chain names, resnames, resids, and atom names must be
    consistent across identifier labels in the workdir in order for this class
    to have the desired behavior.
    """
    def __init__(self, workdir):
        """Load changes from detect_changed_distances for an entire workdir.

        Arguments:
            workdir -- str

        """
        self._trajectory_changes = {}
        for identifier in os.listdir(workdir):
            path = os.path.join(workdir, identifier)
            if os.path.isdir(path) and 'data_info.pkl' in os.listdir(path):
                self._trajectory_changes[identifier] = TrajectoryChanges(
                        workdir, identifier)

    @property
    def identifiers(self):
        """The identifiers in the loaded workdir."""
        identifiers = self._trajectory_changes.keys()
        identifiers.sort()
        return identifiers

    def trajectoryChanges(self, identifier):
        """Retrieve the TrajectoryChanges object for a given identifier.
        
        Arguments:
            identifier -- str

        Returns:
            analyze_changed_distances.TrajectoryChanges

        """
        if identifier not in self._trajectory_changes:
            raise RuntimeError, "Invalid identifier '" + str(identifier) + "'"
        return self._trajectory_changes[identifier]

    @staticmethod
    def _get_common(changes, at_least):
        if at_least is None:
            at_least = len(changes)
        counts = defaultdict(int)
        for change in changes:
            change_set = set()
            for t in change:
                for c in change[t]:
                    if c not in change_set:
                        change_set.add(c)
                        counts[c] += 1
        return set([k for k, v in counts.items() if v >= at_least])

    def commonChanges(self, lam, selection_pair=None, atom_pairs=None,
            residue_pairs=None, at_least=None, identifiers=None):
        """Retrieve changed pairs common to many identifiers in this workdir.

        Calls TrajectoryChanges.changes(lam, selection_pair, atom_pairs,
        residue_pairs) for a given list of identifiers and returns all atom
        pairs for which a change was detected in at least the given number of
        these identifiers. Searches through all identifiers in the workdir if
        'identifiers' is None, and returns pairs that changed for all of the
        given identifiers if 'at_least' is None.

        Arguments:
            lam -- float

            selection_pair -- (str, str), where each str must be a valid atomsel

            atom_pairs -- set( ('(chain)residue:atom', '(chain)residue:atom'), ...)

            residue_pairs -- set( ('(chain)residue', '(chain)residue'), ...)

            at_least -- int

            identifiers -- [str, ..., str]

        Returns:
            set( ('(chain)residue:atom', '(chain)residue:atom'), ... )

        """
        if identifiers is None:
            identifiers = self._trajectory_changes.keys()
        changes = []
        for identifier in identifiers:
            changes.append(self.trajectoryChanges(identifier).changes(lam,
                selection_pair, atom_pairs, residue_pairs))
        return self._get_common(changes, at_least)

    def commonChangesByNumChangeTimes(self, num_change_times,
            selection_pair=None, atom_pairs=None, residue_pairs=None,
            at_least=None, identifiers=None):
        """Retrieve changed pairs common to many identifiers in this workdir.

        Calls TrajectoryChanges.changesByNumChangeTimes(num_change_times,
        selection_pair, atom_pairs, residue_pairs) for a given list of
        identifiers and returns all atom pairs for which a change was detected
        in at least the given number of these identifiers. See docstring for
        'commonChanges' function for more details.
        """
        if identifiers is None:
            identifiers = self._trajectory_changes.keys()
        changes = []
        for identifier in identifiers:
            changes.append(self.trajectoryChanges(
                identifier).changesByNumChangeTimes(num_change_times,
                    selection_pair, atom_pairs, residue_pairs))
        return self._get_common(changes, at_least)

    def commonChangesByNumChanges(self, num_changes, selection_pair=None,
            atom_pairs=None, residue_pairs=None,
            at_least=None, identifiers=None):
        """Retrieve changed pairs common to many identifiers in this workdir.

        Calls TrajectoryChanges.changesByNumChanges(num_changes, selection_pair,
        atom_pairs, residue_pairs) for a given list of identifiers and returns
        all atom pairs for which a change was detected in at least the given
        number of these identifiers.  See docstring for 'commonChanges' function
        for more details.
        """
        if identifiers is None:
            identifiers = self._trajectory_changes.keys()
        changes = []
        for identifier in identifiers:
            changes.append(self.trajectoryChanges(
                identifier).changesByNumChanges(num_changes, selection_pair,
                    atom_pairs, residue_pairs))
        return self._get_common(changes, at_least)

    def commonResidueChanges(self, lam, selection_pair=None,
            atom_pairs=None, residue_pairs=None, at_least=None,
            identifiers=None):
        """Retrieve changed residue pairs common to identifiers in this workdir.

        Calls TrajectoryChanges.changes(lam, selection_pair, atom_pairs,
        residue_pairs) for a given list of identifiers and returns all residue
        pairs for which a change was detected in at least the given number of
        these identifiers. Searches through all identifiers in the workdir if
        'identifiers' is None, and returns pairs that changed for all of the
        given identifiers if 'at_least' is None.

        Arguments:
            lam -- float

            selection_pair -- (str, str), where each str must be a valid atomsel

            atom_pairs -- set( ('(chain)residue:atom', '(chain)residue:atom'), ...)

            residue_pairs -- set( ('(chain)residue', '(chain)residue'), ...)

            at_least -- int

            identifiers -- [str, ..., str]

        Returns:
            set( ('(chain)residue', '(chain)residue'), ... )

        """
        if identifiers is None:
            identifiers = self._trajectory_changes.keys()
        changes = []
        for identifier in identifiers:
            tmp = self.trajectoryChanges(identifier).changes(lam,
                    selection_pair, atom_pairs, residue_pairs)
            changes.append(ChangesToResidueChanges(tmp))
        return self._get_common(changes, at_least)

    def commonResidueChangesByNumChangeTimes(self, num_change_times,
            selection_pair=None, atom_pairs=None, residue_pairs=None,
            at_least=None, identifiers=None):
        """Retrieve changed residue pairs common to identifiers in this workdir.

        Calls TrajectoryChanges.changesByNumChangeTimes(num_change_times,
        selection_pair, atom_pairs, residue_pairs) for a given list of
        identifiers and returns all residue pairs for which a change was
        detected in at least the given number of these identifiers. See
        docstring for 'commonResidueChanges' function for more details.
        """
        if identifiers is None:
            identifiers = self._trajectory_changes.keys()
        changes = []
        for identifier in identifiers:
            tmp = self.trajectoryChanges(identifier).changesByNumChangeTimes(
                    num_change_times, selection_pair, atom_pairs,
                    residue_pairs)
            changes.append(ChangesToResidueChanges(tmp))
        return self._get_common(changes, at_least)

    def commonResidueChangesByNumChanges(self, num_changes, selection_pair=None,
            atom_pairs=None, residue_pairs=None, at_least=None,
            identifiers=None):
        """Retrieve changed residue pairs common to identifiers in this workdir.

        Calls TrajectoryChanges.changesByNumChanges(num_changes, selection_pair,
        atom_pairs, residue_pairs) for a given list of identifiers and returns
        all residue pairs for which a change was detected in at least the given
        number of these identifiers. See docstring for 'commonResidueChanges'
        function for more details.
        """
        if identifiers is None:
            identifiers = self._trajectory_changes.keys()
        changes = []
        for identifier in identifiers:
            tmp = self.trajectoryChanges(identifier).changesByNumChanges(
                    num_changes, selection_pair, atom_pairs, residue_pairs)
            changes.append(ChangesToResidueChanges(tmp))
        return self._get_common(changes, at_least)

def ChangesToResidueChanges(changes):
    """Convert changed atom pairs to changed residue pairs.
    
    Arguments:
        changes -- { frame: set(
            ('(chain)residue:atom', '(chain)residue:atom'), ... )
            , ... 
            }

                                OR

        set( ('(chain)residue:atom', '(chain)residue:atom'), ... )

    Returns:
        { frame: set( ('(chain)residue', '(chain)residue'), ... )
            , ...
            }

                                OR

        set( ('(chain)residue', '(chain)residue'), ... )

    """
    if type(changes) is set:
        return set([(p[0][:p[0].rfind(':')],
            p[1][:p[1].rfind(':')]) for p in changes])
    else:
        residue_changes = {}
        for time in changes:
            residue_changes[time] = set([(p[0][:p[0].rfind(':')],
                p[1][:p[1].rfind(':')]) for p in changes[time]])
        return residue_changes

def VMDDisplay(changes, molid=0, vmd_frames=None, window=5,
        label_before_after=None, observable=None):
    """Display a list of changes in VMD.

    This function only works inside a VMD session, with the trajectory
    containing the given changes loaded into VMD. 'molid' specifies the molecule
    in VMD for this trajectory, and 'vmd_frames' specifies the loaded frames of
    this trajectory in terms of the first frame, last frame, and stride.
    
    Each change is displayed for 'window' frames before and after the change. 
    This display uses two dynamically-updated molreps containing licorice 
    representations of all residues involved in the change and (optionally) 
    dynamically-updated bond labels indicating the changed pairs of atoms. The 
    changed residues are displayed in gray except in the two frames immediately
    preceding and following the change, in which they are colored by element.

    The user may provide a 'label_before_after' function argument to dynamically
    display bond labels corresponding to changed pairs of atoms. The
    'label_before_after' function should take in the median value of a time
    series in a window before the change, the median value of that time series
    in a window after the change, and the pair of atom IDs corresponding to this
    time series, and it should return a pair of boolean values indicating
    whether to display the bond label for this time series before and after the
    change. (The inputs to the 'label_before_after' function may be used to
    selectively display bond labels corresponding to certain types of changes,
    to avoid over-cluttering the VMD display.) By default, no bond labels are
    displayed.

    This function also opens a pyplot window with the change indicator function
    plotted in red, to provide a visual representation of the locations of the
    changes in time and the location of the current frame. An optional
    time series observable may be provided by the 'observable' argument to be 
    plotted in this plot window.

    The atoms loaded in VMD must contain all of the atoms involved in the
    input changes. The dynamic molreps will be reconstructed if they are
    deleted, and the pyplot window will be regenerated if it is closed. To
    permanently delete these molreps, close the pyplot window, and end the
    visual display of these changes, call the VMDClear() function. Only one set
    of changes may be displayed in VMD at a time; a second call to VMDDisplay
    will clear the previous displayed changes.

    Arguments:
        changes -- { frame: set( ('(chain)residue:atom',
            '(chain)residue:atom'), ... )
            , ...
            }

        molid -- int

        vmd_frames -- (first-frame, last-frame, stride, with-structure)
            'first-frame', 'last-frame', and 'stride' are int values indicating
            frames of the original trajectory file input (DCD or DTR/STK) that
            are currently loaded in VMD, and 'with-structure' is a boolean value
            indicating whether frame 0 in VMD is the chemical structure file
            (DMS, MAE, PDB, ...) with frame 1 being the first loaded trajectory
            frame. If None, then it is assumed that all frames of the trajectory
            are loaded and 'with-structure' is True.

        window -- int

        label_before_after -- f(median_before, median_after, aid0, aid1) -> (bool, bool)
            First return value indicates whether to display a bond
            label before the change; second return value indicates
            whether to display a bond label after the change

        observable -- array of observable values to plot, one for each frame
            of the original trajectory file

    """
    import changepoint_vmd
    VMDClear()
    changepoint_vmd._display_changes = changepoint_vmd.DisplayChanges(changes,
            molid, vmd_frames, window, label_before_after, observable)

def VMDClear():
    """Clear the currently displayed changes in VMD."""
    import changepoint_vmd
    if changepoint_vmd._display_changes is not None:
        changepoint_vmd._display_changes.cleanup()
        changepoint_vmd._display_changes = None
