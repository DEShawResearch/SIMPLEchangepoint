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
import molecule
import numpy as np
import changepoint_vmd as cv
from vmd import VMDevaltcl
import unittest
import os


#####################
# Accessing Changes #
#####################
def assertRawChangesDict(d):
    assert isinstance(d, dict)
    for k, v in d.items():
        assert isinstance(k, (int, long, float))
        assert isinstance(v, set)

class TestWorkdirChanges(unittest.TestCase):
    def test_constructor(self):
        from analyze_changed_distances import WorkdirChanges
        wkdir_changes = WorkdirChanges('all_pairs')

    def test_pickIdentifier(self):
        from analyze_changed_distances import WorkdirChanges
        wkdir_changes = WorkdirChanges('all_pairs')
        trj_changes = wkdir_changes.trajectoryChanges('serial')

class TestTrajectoryChanges(unittest.TestCase):
    def test_constructor(self):
        from analyze_changed_distances import TrajectoryChanges
        trj_changes = TrajectoryChanges('all_pairs', 'serial')

    def test_changes(self):
        from analyze_changed_distances import TrajectoryChanges
        trj_changes = TrajectoryChanges('all_pairs', 'serial')
        changes_16 = trj_changes.changes(16)
        assertRawChangesDict(changes_16)

class TestTrajectoryChangesFunctions(unittest.TestCase):
    def setUp(self):
        from analyze_changed_distances import TrajectoryChanges
        trj_changes = TrajectoryChanges('all_pairs', 'serial')
        self.changes = trj_changes.changes(16)

    def test_ChangesToResidueChanges(self):
        from analyze_changed_distances import ChangesToResidueChanges
        x = ChangesToResidueChanges(self.changes)
        assertRawChangesDict(x)

class TestTrajectoryChangesMethods(unittest.TestCase):
    def setUp(self):
        from analyze_changed_distances import TrajectoryChanges
        self.trj_changes = TrajectoryChanges('all_pairs', 'serial')
        self.lam = 16

    def test_selection_pair(self):
        changes_AB = self.trj_changes.changes(self.lam, selection_pair=('chain A and resid 1 to 10',
                                                                        'chain A and resid 11 to 20'))
        assertRawChangesDict(changes_AB)

    def test_atom_pairs(self):
        changes_specific_atoms = self.trj_changes.changes(self.lam, atom_pairs=[('(A)ASP-1:CA', '(A)SER-20:CA'),
                                                                                ('(A)ALA-2:CA', '(A)PRO-19:CA')])
        assertRawChangesDict(changes_specific_atoms)

    def test_residue_pairs(self):
        changes_specific_residues = self.trj_changes.changes(self.lam, residue_pairs=[('(A)ASP-1', '(A)SER-20'),
                                                                                     ('(A)ALA-2', '(A)PRO-19')])
        assertRawChangesDict(changes_specific_residues)

####################
# Plotting changes #
####################
class TestPlotting(unittest.TestCase):
    def setUp(self):
        from analyze_changed_distances import TrajectoryChanges
        self.trj_changes = TrajectoryChanges('all_pairs', 'serial')
        self.lam = 16

    def test_plotDistance(self):
        self.trj_changes.plotDistance(('(A)ASP-1:CA', '(A)SER-20:CA'), lam=self.lam)

    def test_matrixPlotChange(self):
        changes = self.trj_changes.changes(self.lam)
        v = changes.values()[0]
        self.trj_changes.matrixPlotChange(v, lam=self.lam)


##############################
# Visualizing changes in VMD #
##############################
class TestVMDDisplay(unittest.TestCase):
    def setUp(self):
        from analyze_changed_distances import WorkdirChanges
        wkdir_changes = WorkdirChanges('all_pairs')
        common_changes = wkdir_changes.commonResidueChangesByNumChangeTimes(100)
        self.changes = wkdir_changes.trajectoryChanges('serial').changesByNumChangeTimes(100, residue_pairs=common_changes)
        assert len(self.changes)

    def test_VMDDisplay(self):
        from analyze_changed_distances import VMDDisplay
        VMDDisplay(self.changes, window=5, molid=0)


if __name__ == '__main__':
    os.chdir(os.getenv('EXAMPLESDIR', 'examples'))
    molid = molecule.load('mae', 'TrpCage.mae')
    VMDevaltcl('mol addfile {TrpCage.dcd} type {dcd} first 0 last -1 step 1 waitfor all 0')
    cv.set_times(molid, np.loadtxt('TrpCage.times.txt'))
    unittest.main(verbosity=2)
