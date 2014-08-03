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
import numpy as np
import SIMPLEchangepoint
import unittest
import os

# Run deterministic test case involving pseudorandom data that should be
# easy enough that machine precision details don't affect whether the
# correct (exact/approximate) answer is obtained.

def _exact(got, expect):
    eq = got == expect
    assert eq, "got %s, expected %s" % (got.__repr__(), expect.__repr__())

def _approx(got, expect, abstol=None):
    s = "got %s, expected %s" % (got.__repr__(), expect.__repr__())
    if not np.iterable(expect):
        relerr = abs(got-expect) / float(expect)
        assert relerr <= 0.1, 'relative error exceeds 10%%: %s' % s
        return
    if isinstance(expect, set):
        sens = len(got & expect) / float(len(expect))
        spec = len(got & expect) / float(len(got))
        assert sens >= 0.9, 'sensitivity < 90%%: %s' % s
        assert spec >= 0.9, 'specificity < 90%%: %s' % s
        return
    if isinstance(expect, list):
        assert len(got) == len(expect)
        for g, e in zip(got, expect):
            assert abs(g-e)<=abstol, 'difference exceeds %d: %s' % (abstol, s)


np.random.seed(20140001)
data = np.random.randn(100, 1000)
data[:5, 500:] += 1 # 5/100 traces change together
data[6:8, :200] += 1 # 2/100 traces change together
changes = SIMPLEchangepoint.ComputeChanges(data, lam=32)

class TestMeanChangeIIDGaussian(unittest.TestCase):
    def setUp(self):
        self.changes = changes

    def test_exact_numchanges(self):
        _exact(len(self.changes), 2)

    def test_approx_changetimes(self):
        _approx(sorted(self.changes.keys()), [200, 500], 10)

    def test_exact_changed_traces1(self):
        _exact(len(self.changes), 2)
        _exact(sorted(self.changes.items())[0][1], set(range(6,8)))

    def test_exact_changed_traces2(self):
        _exact(len(self.changes), 2)
        _exact(sorted(self.changes.items())[1][1], set(range(5)))


np.random.seed(20140002)
data2 = np.random.laplace(loc=0, scale=1.0, size=(100*1000)).reshape(100,1000)
data2[10:15, 500:] += 1
data2[15:17, 600:] += 2
changes2 = SIMPLEchangepoint.ComputeChanges(data2, lam=32)

class TestMeanChangeIIDLaplace(unittest.TestCase):
    def setUp(self):
        self.changes = changes2

    def test_exact_numchanges(self):
        _exact(len(self.changes), 2)

    def test_approx_changetimes(self):
        _approx(sorted(self.changes.keys()), [500, 600], 10)

    def test_exact_changed_traces1(self):
        _exact(len(self.changes), 2)
        _exact(sorted(self.changes.items())[0][1], set(range(10, 15)))

    def test_exact_changed_traces2(self):
        _exact(len(self.changes), 2)
        _exact(sorted(self.changes.items())[1][1], set(range(15, 17)))


np.random.seed(20140003)
data3 = np.random.randn(100, 1000)
data3[60:80, 500:] *= 2
data3[80:82, 800:] *= 3
changes3 = SIMPLEchangepoint.ComputeChanges(data3, lam=32)

class TestVarianceChangeIIDGaussian(unittest.TestCase):
    def setUp(self):
        self.changes = changes3

    def test_exact_numchanges(self):
        _exact(len(self.changes), 2)

    def test_approx_changetimes(self):
        _approx(sorted(self.changes.keys()), [500, 800], 10)

    def test_exact_changed_traces1(self):
        _exact(len(self.changes), 2)
        _exact(sorted(self.changes.items())[0][1], set(range(60, 80)))

    def test_exact_changed_traces2(self):
        _exact(len(self.changes), 2)
        _exact(sorted(self.changes.items())[1][1], set(range(80, 82)))


np.random.seed(20140004)
data4 = np.random.laplace(loc=0, scale=1.0, size=(100*1000)).reshape(100,1000)
data4[70:80, 500:] *= 2
data4[80:82, 800:] *= 3
changes4 = SIMPLEchangepoint.ComputeChanges(data4, lam=32)

class TestVarianceChangeIIDLaplace(unittest.TestCase):
    def setUp(self):
        self.changes = changes4

    def test_exact_numchanges(self):
        _exact(len(self.changes), 2)

    def test_approx_changetimes(self):
        _approx(sorted(self.changes.keys()), [500, 800], 10)

    def test_exact_changed_traces1(self):
        _exact(len(self.changes), 2)
        _exact(sorted(self.changes.items())[0][1], set(range(70, 80)))

    def test_exact_changed_traces2(self):
        _exact(len(self.changes), 2)
        _exact(sorted(self.changes.items())[1][1], set(range(80, 82)))


np.random.seed(20140005)
data5 = []
m = 0.9
r = np.zeros(100, np.float32)
for i in range(1100):
    r = r*m
    r += np.random.randn(100)
    data5.append(r) # variance = 1 / (1 - m**2)
data5 = np.transpose(data5[100:]) * (1-m**2)
data5[20:40, 500:] += 1
data5[60:70, 600:] += 1
changes5 = SIMPLEchangepoint.ComputeChanges(data5, lam=512)

class TestMeanChangeOU(unittest.TestCase):
    def setUp(self):
        self.changes = changes5

    def test_exact_numchanges(self):
        _exact(len(self.changes), 2)

    def test_approx_changetimes(self):
        _approx(sorted(self.changes.keys()), [500, 600], 10)

    def test_approx_changed_traces1(self):
        _approx(len(self.changes), 2)
        _approx(sorted(self.changes.items())[0][1], set(range(20, 40)))

    def test_approx_changed_traces2(self):
        _approx(len(self.changes), 2)
        _approx(sorted(self.changes.items())[1][1], set(range(60, 70)))


np.random.seed(20140006)
data6 = []
m = 0.9
r = np.zeros(100, np.float32)
for i in range(1100):
    r = r*m
    r += np.random.randn(100)
    data6.append(r) # variance = 1 / (1 - m**2)
data6 = np.transpose(data6[100:]) * (1-m**2)
data6[20:40, 300:] *= 3
data6[60:65, 798:] *= 3
data6[65:70, 802:] *= 3 # should coalesce with traces 60-64
changes6 = SIMPLEchangepoint.ComputeChanges(data6, lam=256)

class TestVarianceChangeOU(unittest.TestCase):
    def setUp(self):
        self.changes = changes6

    def test_exact_numchanges(self):
        _exact(len(self.changes), 2)

    def test_approx_changetimes(self):
        _approx(sorted(self.changes.keys()), [300, 800], 10)

    def test_approx_changed_traces1(self):
        _approx(len(self.changes), 2)
        _approx(sorted(self.changes.items())[0][1], set(range(20, 40)))

    def test_approx_changed_traces2(self):
        _approx(len(self.changes), 2)
        _approx(sorted(self.changes.items())[1][1], set(range(60, 70)))


ut_data = dict(MeanChangeIIDGaussian=(data, changes),
               MeanChangeIIDLapalce=(data2, changes2),
               VarianceChangeIIDGaussian=(data3, changes3),
               VarianceChangeIIDLaplace=(data4, changes4),
               MeanChangeOU=(data5, changes5),
               VarianceChangeOU=(data6, changes6))

import cPickle, os
s = os.path.realpath('tests/all_ut_data.pkl')
print '\nWriting unit test data:\n  %s' % s
cPickle.dump(ut_data, open(s, 'w'), -1)

# for user to test executables
cPickle.dump(data, open('tests/data.pkl', 'w'), -1)
print '  %s' % os.path.realpath('tests/data.pkl')

try:
    import tables
    h5 = tables.openFile('tests/data.h5', 'w')
    ca = h5.createCArray(h5.root, 'data', tables.Float64Atom(), data.shape)
    ca[:] = data
    h5.close()
    print '  %s' % os.path.realpath('tests/data.h5')
except ImportError:
    pass
print ''

if __name__ == '__main__':
    unittest.main(verbosity=2)
