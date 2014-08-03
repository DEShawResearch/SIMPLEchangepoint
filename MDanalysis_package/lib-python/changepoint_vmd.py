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
import vmd
import molecule
from atomsel import atomsel
import molrep
import label
import vmdcallbacks
import sys
import os
import re

import copy
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

import gtk
vmdcallbacks.add_callback('display_update',
        lambda: gtk.main_iteration(block=False))

def set_times(molid, times):
    import molecule
    offset = molecule.numframes(molid) - len(times)
    assert offset == 1 or offset == 0 # frame 0 may be the system file
    for i, t in enumerate(times):
        molecule.set_physical_time(t, molid, i+offset)

class Timekeeper(object):
    def __init__(self, molid):
        self.connected = list()
        self.molid = molid
        vmdcallbacks.add_callback('frame', lambda molid, frame,
                s=self: s.update(molid, frame))
        self.current_frames = None
        self.old_frame = None

    def update(self, molid, frame, debug=False):
        # exception handling so as not to crash the callback system
        try:
            if molid != self.molid or frame == -1: return
            # be careful -- self.connected may change during draw calls
            conn = copy.copy(self.connected)
            for c in conn:
                c.showtime(frame, self.old_frame)
            self.old_frame = frame
        except Exception, e:
            print 'ChangepointVMD exception'
            print e.__class__.__name__ + ': ' + str(e)

    def register(self, obj):
        self.connected.append(obj)

    def unregister(self, obj):
        try:
            self.connected.remove(obj)
        except ValueError:    # value not in list
            pass

_timekeepers = dict()
def timekeeper(molid):
    global _timekeepers
    if molid not in _timekeepers:
        _timekeepers[molid] = Timekeeper(molid)
    return _timekeepers[molid]

class DisplayChanges(object):
    def _info_to_ids(self, info):
        pattern = re.compile(r"^\((?P<chain>[^()]*)\)(?P<resname>.+)-(?P<resid>\d+):(?P<atomname>[^:]+)$")
        match = pattern.match(info)
        if match is None:
            raise RuntimeError, "Misformatted info string: '%s'" % info
        ids = []
        for name in match.group('atomname').split('/'):
            sel_str = 'chain %s and resname %s and resid %d and name %s' \
                    % (match.group('chain'), match.group('resname'),
                        int(match.group('resid')), name)
            atoms = atomsel(sel_str).get('index')
            if len(atoms) == 0:
                raise RuntimeError, \
                        "Selection '%s' does not specify a valid atom" % sel_str
            elif len(atoms) > 1:
                print >> sys.stderr, \
                        "WARNING: Selection '%s' specifies more than one atom" \
                        % sel_str
            ids.append(atoms[0])
        return tuple(sorted(ids))

    def __init__(self, changes, molid, vmd_frames, window, label_before_after, 
            observable):
        if molid not in molecule.listall():
            raise RuntimeError, "Invalid molid %d" % molid
        self.molid = molid
        self.tk = timekeeper(molid)
        self.tk.register(self)

        self.disp_h = False
        self.changes = {}
        for time, change in changes.items():
            # Map change time (frame in original trajectory file) to VMD frame
            if vmd_frames is None:
                vmd_time = time + 1
            else:
                if len(vmd_frames) != 4 or vmd_frames[0] >= vmd_frames[1] or \
                        vmd_frames[0] < 0 or vmd_frames[2] < 1:
                    raise RuntimeError, "Invalid vmd_frames input"
                vmd_time = (float(time) - vmd_frames[0]) / vmd_frames[2]
                if vmd_time < 0 or vmd_time > vmd_frames[1]:
                    continue
                if vmd_frames[3]:
                    vmd_time += 1
            self.changes[vmd_time]=change
            for pair in change:
                a0_all = self._info_to_ids(pair[0])
                a1_all = self._info_to_ids(pair[1])
                for a0 in a0_all:
                    for a1 in a1_all:
                        if atomsel('index %d' % a0).get('element') == 'H' and \
                                'C' not in atomsel('withinbonds 1 of index %d'
                                        % a0).get('element'):
                            self.disp_h = True
                        if atomsel('index %d' % a1).get('element') == 'H' and \
                                'C' not in atomsel('withinbonds 1 of index %d'
                                        % a1).get('element'):
                            self.disp_h = True
        self.change_times = sorted(self.changes.keys())
        self.loaded_frames = False

        # To display residues and lines in VMD
        self.window = window
        self.label_before_after = label_before_after
        self.pairs = []
        self.gray_res_sels = []
        self.color_res_sels = []
        molrep.addrep(self.molid, style='Licorice', color='ColorID 2',
                selection='none', material='Opaque')
        self.gray_rep = molrep.get_repname(self.molid, molrep.num(self.molid)-1)
        molrep.addrep(self.molid, style='Licorice', color='Element',
                selection='none', material='Opaque')
        self.color_rep = molrep.get_repname(self.molid, molrep.num(self.molid)-1)

        # To plot an indicator variable with a moving line
        self.fig = None
        self.ax = None
        self.line = None
        self.observable = observable
        if observable is not None:
            ymin = min(observable)
            ymax = max(observable)
            self.ylim = (1.1 * ymin - 0.1 * ymax, 1.1 * ymax - 0.1 * ymin)
        else:
            self.ylim = (0,2)

    def replot(self):
        if self.fig is None or self.ax is None:
            return
        self.ax.cla()
        self.ax.set_xlabel('Frame')
        if self.observable is not None:
            self.ax.plot(self.observable, 'r.')
        self.ax.plot(self.change_times, 0.5 * (self.ylim[0] + self.ylim[1])
                * np.ones(len(self.change_times)), 'ro')
        self.ax.set_xlim((0, molecule.numframes(self.molid)))
        self.ax.set_ylim(self.ylim)
        self.fig.canvas.draw()
        self.dataplot = self.fig.canvas.copy_from_bbox(self.ax.bbox)

    def showtime(self, frame, old_frame):
        if not self.loaded_frames:
            # Initialize display
            self.loaded_frames = True
            numframes = molecule.numframes(self.molid)
            self.pairs = [set() for i in range(numframes)]
            self.gray_res_sels = ['none' for i in range(numframes)]
            self.color_res_sels = ['none' for i in range(numframes)]
            first_frame = 0
            for i, time in enumerate(self.change_times):
                while first_frame < numframes and first_frame < time:
                    first_frame += 1
                if first_frame > numframes - min(6, self.window + 1):
                    break
                if first_frame < min(5, self.window):
                    continue
                begin = max(first_frame - self.window, 0)
                for j in range(i-1,-1,-1):
                    if self.change_times[j] <= begin:
                        break
                    if len(self.changes[self.change_times[j]] & self.changes[self.change_times[i]]) > 0:
                        begin = 0
                        while begin < first_frame and begin < self.change_times[j]:
                            begin += 1
                        break
                end = min(first_frame + self.window, numframes)
                for j in range(i+1, len(self.change_times)):
                    if self.change_times[j] > end-1:
                        break
                    if len(self.changes[self.change_times[j]] & self.changes[self.change_times[i]]) > 0:
                        end = numframes
                        while end > first_frame and end-1 >= self.change_times[j]:
                            end -= 1
                        break
                if begin >= first_frame or end <= first_frame + 1:
                    continue
                all_changed = []
                for pair in self.changes[time]:
                    a0_all = self._info_to_ids(pair[0])
                    a1_all = self._info_to_ids(pair[1])
                    for a0 in a0_all:
                        for a1 in a1_all:
                            before_dists = [float(v) for v in vmd.VMDevaltcl(
                                'measure bond {%d %d} molid %d first %d last %d'
                                % (a0, a1, self.molid, begin,
                                    first_frame-1)).split()]
                            before_med = np.median(before_dists)
                            after_dists = [float(v) for v in vmd.VMDevaltcl(
                                'measure bond {%d %d} molid %d first %d last %d' 
                                % (a0, a1, self.molid, first_frame,
                                    end-1)).split()]
                            after_med = np.median(after_dists)
                            if self.label_before_after is not None:
                                label_before, label_after = \
                                        self.label_before_after(
                                                before_med, after_med, a0, a1)
                            else:
                                label_before = False
                                label_after = False
                            if label_before:
                                self.pairs[first_frame-1].add((a0,a1))
                            if label_after:
                                self.pairs[first_frame].add((a0,a1))
                    all_changed += list(a0_all) + list(a1_all)
                for f in range(begin, end):
                    sel = 'same residue as index'
                    for changed_atom in all_changed:
                        sel += ' %d' % changed_atom
                    if self.disp_h:
                        sel = ' or (%s)' % sel
                    else:
                        sel = ' or ((' + sel + ') and not (element H and' + \
                            ' withinbonds 1 of element C))'
                        if f == first_frame - 1 or f == first_frame:
                            self.color_res_sels[f] += sel
                        else:
                            self.gray_res_sels[f] += sel
            old_frame = None
        gray_repid = molrep.repindex(self.molid, self.gray_rep)
        if gray_repid == -1:
            # User deleted molrep to display residues--recreate this molrep
            molrep.addrep(self.molid, style='Licorice', color='ColorID 2',
                    selection='none', material='Opaque')
            self.gray_rep = molrep.get_repname(self.molid,
                    molrep.num(self.molid)-1)
            gray_repid = molrep.repindex(self.molid, self.gray_rep)
            old_frame = None
        color_repid = molrep.repindex(self.molid, self.color_rep)
        if color_repid == -1:
            # User deleted molrep to display residues--recreate this molrep
            molrep.addrep(self.molid, style='Licorice', color='Element',
                    selection='none', material='Opaque')
            self.color_rep = molrep.get_repname(self.molid,
                    molrep.num(self.molid)-1)
            color_repid = molrep.repindex(self.molid, self.color_rep)
            old_frame = None
        if old_frame is None \
                or self.gray_res_sels[old_frame] != self.gray_res_sels[frame]:
            molrep.modrep(self.molid, gray_repid, sel=self.gray_res_sels[frame])
        if old_frame is None or \
                self.color_res_sels[old_frame] != self.color_res_sels[frame]:
            molrep.modrep(self.molid, color_repid,
                    sel=self.color_res_sels[frame])
        if old_frame is None or self.pairs[old_frame] != self.pairs[frame]:
            labels = label.listall(label.BOND)
            for l in labels:
                label.delete(label.BOND, l)
            os.environ['VMD_QUIET_STARTUP'] = '1'
            molid_pair = (self.molid, self.molid)
            for pair in self.pairs[frame]:
                label.add(label.BOND, molid_pair, pair)
            os.environ.pop('VMD_QUIET_STARTUP')

        # Update plot of indicator variable
        if self.fig is None or self.fig.canvas.window is None:
            # Figure has not been created or was closed by user--create new
            # figure
            self.fig = plt.figure()
            # Need to replot everything if the figure window is resized
            self.fig.canvas.mpl_connect('resize_event', lambda ev,
                    s=self: s.replot())
            self.fig.show()
            self.ax = self.fig.add_subplot(111)
            self.line = self.ax.axvline(0, animated=True, color='r',
                    linewidth=2)
            self.replot()
        self.fig.canvas.restore_region(self.dataplot)
        self.line.set_xdata(frame)
        self.ax.draw_artist(self.line)
        self.fig.canvas.blit(self.ax.bbox)

    def cleanup(self):
        repid = molrep.repindex(self.molid, self.gray_rep)
        if repid != -1:
            molrep.delrep(self.molid, repid)
        repid = molrep.repindex(self.molid, self.color_rep)
        if repid != -1:
            molrep.delrep(self.molid, repid)
        labels = label.listall(label.BOND)
        for l in labels:
            label.delete(label.BOND, l)
        if self.fig is not None:
            plt.close(self.fig)
        self.tk.unregister(self)

_display_changes = None
