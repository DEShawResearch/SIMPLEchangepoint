/*
Copyright 2012-2014, D. E. Shaw Research.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions, and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions, and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

* Neither the name of D. E. Shaw Research nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
#include <Python.h>
#include <numpy/arrayobject.h>
#include <assert.h>
#include <math.h>
#include <stdlib.h>
#include <queue>
#include <list>
#include <string>
#include <iostream>
#include <limits>

const int MIN_SEP = 2;

struct SuffStat {
    SuffStat(int _t) : t(_t), n(0), med(0), total_var(0), cost(0), prune_t(-1) {}

    void add(double x) {
        ++n;
        if (highs.size() == lows.size()) {
            if (highs.size() == 0 || x < highs.top()) {
                lows.push(x);
                med = lows.top();
                total_var += med - x;
            } else {
                highs.push(x);
                med = highs.top();
                total_var += x - med;
            }
        } else if (highs.size() < lows.size()) {
            if (x >= lows.top()) {
                highs.push(x);
                med = (lows.top() + highs.top()) / 2;
                total_var += (highs.top() - lows.top()) / 2;
                total_var += x - med;
            } else {
                highs.push(lows.top());
                lows.pop();
                lows.push(x);
                med = (lows.top() + highs.top()) / 2;
                total_var += (highs.top() - lows.top()) / 2;
                total_var += med - x;
            }
        } else {
            if (x <= highs.top()) {
                lows.push(x);
                med = (lows.top() + highs.top()) / 2;
                total_var += (highs.top() - lows.top()) / 2;
                total_var += med - x;
            } else {
                lows.push(highs.top());
                highs.pop();
                highs.push(x);
                med = (lows.top() + highs.top()) / 2;
                total_var += (highs.top() - lows.top()) / 2;
                total_var += x - med;
            }
        }
    }

    double ll() {
        if (total_var == 0 || n < MIN_SEP)
            return -std::numeric_limits<double>::infinity();
        else
            return -n * (1 + log(2 * total_var / n));
    }

    std::priority_queue<double, std::vector<double>, std::greater<double> > highs;
    std::priority_queue<double, std::vector<double>, std::less<double> > lows;
    int t;
    int n;
    double med;
    double total_var;
    double cost;
    int prune_t;
};

static PyObject* find_changes(PyObject* self, PyObject* args) {
    PyObject* arg1 = NULL;
    PyObject* arg2 = NULL;
    if (!PyArg_ParseTuple(args, "OO", &arg1, &arg2)) return NULL;
    PyObject* np_data = PyArray_FROM_OTF(arg1, NPY_FLOAT32, NPY_IN_ARRAY);
    PyObject* np_penalties = PyArray_FROM_OTF(arg2, NPY_FLOAT32, NPY_IN_ARRAY);
    if (np_data == NULL || np_penalties == NULL) {
        Py_XDECREF(np_data);
        Py_XDECREF(np_penalties);
        return NULL;
    }
    int T = PyArray_DIM(np_data, 0);
    if (T != PyArray_DIM(np_penalties, 0) + 1) {
        PyErr_SetString(PyExc_ValueError, "Dimensions of data and penalty are not compatible");
        Py_DECREF(np_data);
        Py_DECREF(np_penalties);
        return NULL;
    }
    float* data = (float*) PyArray_DATA(np_data);
    float* penalties = (float*) PyArray_DATA(np_penalties);
    double* vals = new double[T];
    int* prev = new int[T];
    std::list<SuffStat> checks;
    checks.push_back(SuffStat(0));
    for (int t = 0; t < MIN_SEP - 1; ++t)
        checks.back().add(data[t]);
    for (int t = MIN_SEP - 1; t < T; ++t) {
        double max_val = -std::numeric_limits<double>::max();
        int max_ind = -1;
        for (std::list<SuffStat>::iterator iter = checks.begin(); iter != checks.end(); ++iter) {
            if (iter->prune_t == t) {
                iter = checks.erase(iter);
                --iter;
                continue;
            }
            iter->add(data[t]);
            double val = iter->ll();
            if (iter->t > 0)
                val += vals[iter->t - 1] - penalties[iter->t - 1];
            iter->cost = val;
            if (val > max_val) {
                max_val = val;
                max_ind = iter->t;
            }
        }
        vals[t] = max_val;
        prev[t] = max_ind;
        for (std::list<SuffStat>::iterator iter = checks.begin(); iter != checks.end(); ++iter) {
            if (t < T-1 && iter->prune_t == -1 && iter->cost < vals[t] - penalties[t])
                iter->prune_t = t + MIN_SEP;
        }
        if (t - MIN_SEP + 2 >= MIN_SEP) {
            checks.push_back(SuffStat(t-MIN_SEP+2));
            for (int s = t - MIN_SEP + 2; s <= t; ++s)
                checks.back().add(data[s]);
        }
    }
    PyObject* changes = PyList_New(0);
    int ind = prev[T-1];
    while (ind > 1) {
        PyObject* num = PyInt_FromLong(ind);
        PyList_Append(changes, num);
        Py_DECREF(num);
        ind = prev[ind-1];
    }
    PyList_Reverse(changes);
    delete[] vals;
    delete[] prev;
    Py_DECREF(np_data);
    Py_DECREF(np_penalties);
    return changes;
}

static PyObject* ll_difference(PyObject* self, PyObject* args) {
    PyObject* arg1 = NULL;
    int prev_change, next_change, start, end;
    if (!PyArg_ParseTuple(args, "Oiiii", &arg1, &prev_change,
                &next_change, &start, &end)) return NULL;
    PyObject* np_data = PyArray_FROM_OTF(arg1, NPY_FLOAT32, NPY_IN_ARRAY);
    if (np_data == NULL) return NULL;
    int T = PyArray_DIM(np_data, 0);
    if (start < 0 || start >= end || T < end) {
        PyErr_SetString(PyExc_ValueError, "Dimensions of data are not compatible with start and end values");
        Py_DECREF(np_data);
        return NULL;
    }
    float* data = (float*) PyArray_DATA(np_data);
    npy_intp out_dims[1];
    *out_dims = end - start + 1;
    PyObject* np_ll_diff = PyArray_SimpleNew(1, out_dims, NPY_FLOAT64);
    double* ll_diff = (double*) PyArray_DATA(np_ll_diff);
    if (prev_change == start)
        ll_diff[0] = 0;
    SuffStat tmp(0);
    for (int t = prev_change; t < next_change; ++t) {
        tmp.add(data[t]);
        if (t >= start-1 && t < end)
            ll_diff[t-start+1] = tmp.ll();
    }
    double prev_ll = tmp.ll();
    if (prev_ll == -std::numeric_limits<double>::infinity()) {
        Py_DECREF(np_data);
        return np_ll_diff;
    }
    if (next_change == end)
        ll_diff[end - start] -= prev_ll;
    tmp = SuffStat(0);
    for (int t = next_change - 1; t >= start; --t) {
        tmp.add(data[t]);
        if (t <= end)
            ll_diff[t-start] += tmp.ll() - prev_ll;
    }
    Py_DECREF(np_data);
    return np_ll_diff;
}

static PyMethodDef methods[] = {
    {"find_changes", find_changes, METH_VARARGS, "univariate dynamic programming algorithm"},
    {"ll_difference", ll_difference, METH_VARARGS, "compute log-likelihood differences"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
init_univariate_changes(void) {
    (void)Py_InitModule("_univariate_changes", methods);
    import_array();
}
