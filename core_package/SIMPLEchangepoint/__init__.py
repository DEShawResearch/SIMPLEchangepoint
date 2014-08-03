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
import scipy.sparse
from collections import defaultdict
import _univariate_changes
import sys

def ComputeChanges(data, lam, alpha=0.7, groups=None, beta=1.0, lam_min=None,
                   verbose=True, parallel=False, seeds=None, max_iters=100):
    """Computes simultaneous change-points in multiple time series.

    Fits a model in which data in each segment between change-points for each
    time series is iid Laplace distributed, and these segments are independent.
    Selects the model by maximizing the log-likelihood of the data, subject to
    a penalty for each change time equal to

        p(S) = lam*(sum_{G in groups} |S intersect G|^beta)^alpha,

    where S is the set of changed time series at that time.

    Arguments:
        data -- 2-dimensional (J x T) numpy array, where J is the number of time
            series observables and T is the length of each time series. For
            large data sets, HDF5 CArrays and EArrays are supported using
            PyTables. For optimal performance, array should be of type 'float32'
            and in C-contiguous order, and chunk shape should be (1 x T) for
            HDF5 CArrays or EArrays.

        lam -- Positive real-valued sensitivity parameter. Set lam
            higher to detect fewer changes, and lower to detect more
            changes.

        alpha -- Parameter in (0,1]. Set alpha closer to 0 to increase the
            tendency of detecting changes in different time series as
            simultaneous, and closer to 1 to decrease this tendency.

        groups -- List of (not necessarily disjoint) subsets of time series, in
            the format [ set(int, ..., int), ..., set(int, ..., int) ] where
            each set specifies indices in the range 0, ..., J-1. Changes will
            have a greater tendency of being detected as simultaneous for time
            series within the same subsets. If None, defaults to
            [ set(1, ..., J) ].

        beta -- Parameter in (0,1]. Set beta closer to 0 to increase the
            tendency of detecting changes within the same groups as
            simultaneous, and closer to 1 to decrease this tendency.

        lam_min -- Positive real-valued sensitivity parameter that
            limits the reduced penalties used for the first iteration.
            Defaults to 8.  Set to 0 to disable.

            NOTE: the lam_min=8 option was not used in the analysis
            reported in the paper by Fan et al, as this option was
            introduced after the analysis was performed. We find the
            default setting lam_min=8 to improve algorithm runtime in
            the first iteration without affecting changepoint
            detection accuracy.


        verbose -- Print algorithm progress to screen.

        parallel -- Set to True if the algorithm is being called in parallel
            on multiple nodes using MPI.

        seeds -- Random-number-generator seeds for randomization of marginal
            penalty values, in the format [seed_0, ..., seed_{J-1}]. If None,
            defaults to [0, ..., J-1].

        max_iters -- Maximum number of iterations for which to run algorithm.

    Returns:
        { int: set(int, ..., int), ..., int: set(int, ..., int) } where a key of
            t indicates a change time between data points t-1 and t, and the
            set value for that key indicates the observables (a subset of
            {0,...,J-1}) that change at that time.

    """
    if parallel:
        from mpi4py import MPI
        world = MPI.COMM_WORLD
        world_size = world.Get_size()
        world_rank = world.Get_rank()
    else:
        world_size = 1
        world_rank = 0
    if world_rank == 0:
        assert len(data.shape) == 2, 'Data must be 2-dimensional.'
    J = int(data.shape[0])
    T = int(data.shape[1])
    if lam_min == None:
        lam_min = 8
        if world_rank == 0:
            print 'Chose lam_min=%g by default' % lam_min

    if verbose and world_rank == 0:
        print 'World size: ' + str(world_size)
        print str(J) + ' time series'
        print str(T) + ' frames'

    # Divide time series across nodes
    if verbose and world_rank == 0:
        print 'Reading data'
    inds = range(world_rank, J, world_size)
    if groups is None:
        groups = [set(range(J))]
    if len(inds) > 0:
        data = np.array(data[inds,:], dtype='float32', order='C')
        group_inds = [[i for i, group in enumerate(groups) if ind in group]
                for ind in inds]

    if world_rank == 0:
        group_sizes = np.zeros(len(groups), dtype='int')
        for g_ind, group in enumerate(groups):
            group_sizes[g_ind] = len(group)
        if np.max(group_sizes) <= 255:
            group_dtype = np.uint8
        elif np.max(group_sizes) <= 65535:
            group_dtype = np.uint16
        else:
            group_dtype = np.uint32
        groups_mat = scipy.sparse.lil_matrix((len(groups), J), dtype=group_dtype)
        for g_ind, group in enumerate(groups):
            groups_mat[g_ind, list(group)] = 1
        groups_mat = groups_mat.tocsr()
    else:
        groups_mat = None
        group_sizes = None
        group_dtype = None
    if parallel:
        groups_mat = world.bcast(groups_mat, 0)
        group_sizes = world.bcast(group_sizes, 0)
        group_dtype = world.bcast(group_dtype, 0)

    # Define penalty function
    def penalty_func(changes):
        return lam * (sum([(len(changes & group)) ** beta
            for group in groups])) ** alpha

    if world_rank == 0:
        change_history = []
        if verbose:
            print 'Starting iteration 0'
            sys.stdout.write('...initializing penalties ')
            sys.stdout.flush()

    if len(inds) > 0:
        # For first iteration, use random penalties between
        # 0.9 * minimum marginal penalty and 1.0 * minimum marginal penalty
        rands = np.zeros((len(inds), T-1), dtype='float32', order='C')
        penalties = np.zeros((len(inds), T-1), dtype='float32', order='C')
        current = sum(group_sizes**beta)
        for i, ind in enumerate(inds):
            if seeds is None:
                np.random.seed(ind)
            else:
                np.random.seed(seeds[ind])
            rands[i] = np.random.uniform(0.9, 1, T-1)
            new = current - sum(group_sizes[group_inds[i]]**beta) \
                    + sum((group_sizes[group_inds[i]]-1)**beta)
            if new < 0:
                new = 0
            penalties[i] = lam * (current**alpha - new**alpha) * rands[i]
        mask = penalties < (0.9 * lam_min)
        penalties[mask] = rands[mask] * lam_min
        Nraise, Ntot = mask.sum(), mask.size
        if parallel:
            lst = world.gather((Nraise, Ntot), 0)
            if world_rank == 0:
                Nraise, Ntot = np.sum(lst, axis=0)
        if world_rank == 0:
            fmt = "(raised %d/%d penalties using lam_min=%g)\n"
            sys.stdout.write(fmt % (Nraise, Ntot, lam_min))

    prev_nchange_times = T
    shift_and_merge = False
    disabled = [False for i in range(len(inds))]
    for iter in range(max_iters):
        # Compute new changes using previous penalties
        if verbose and world_rank == 0:
            print '...computing changepoints marginally'
        new_changes = defaultdict(set)
        changes_per_ind = []
        for i, ind in enumerate(inds):
            if not disabled[i]:
                try:
                    changes_per_ind.append(_univariate_changes.find_changes(
                        data[i], penalties[i]))
                except MemoryError:
                    print 'Memory error in observable ' + str(ind)
                    raise
            else:
                changes_per_ind.append([])
            if iter == 0 and len(changes_per_ind[-1]) == 0:
                disabled[i] = True
            changes_per_ind[-1] = [0] + changes_per_ind[-1] + [T]
            for t in changes_per_ind[-1]:
                new_changes[t].add(ind)
        if verbose and world_rank == 0 and parallel:
            print '...gathering changepoints'
        if parallel:
            all_new_changes = world.gather(new_changes, 0)
        else:
            all_new_changes = [new_changes]
        changes = defaultdict(set)
        if world_rank == 0:
            for new_changes in all_new_changes:
                for t, changed_inds in new_changes.iteritems():
                    changes[t].update(changed_inds)
            if verbose and parallel:
                print '...broadcasting combined changes'
        if parallel:
            changes = world.bcast(changes, 0)

        # Shift change times
        if len(changes) < T-1 and len(changes) >= prev_nchange_times:
            shift_and_merge = True
        if shift_and_merge:
            if verbose and world_rank == 0:
                print '...shifting/merging change times'
            change_times = changes.keys()
            change_times.sort()
            prev_change_ind = [0] * len(inds)
            next_change_ind = [0] * len(inds)
            t = 0
            while t < len(change_times) - 2:
                ll_diffs = np.zeros((len(inds), change_times[t+2]
                    - change_times[t]+1), dtype='float64')
                for i, ind in enumerate(inds):
                    while changes_per_ind[i][prev_change_ind[i]+1] \
                            <= change_times[t]:
                        prev_change_ind[i] += 1
                    while changes_per_ind[i][next_change_ind[i]] \
                            < change_times[t+2]:
                        next_change_ind[i] += 1
                    if ind not in changes[change_times[t+1]]:
                        continue
                    ll_diffs[i] = _univariate_changes.ll_difference(data[i],
                            changes_per_ind[i][prev_change_ind[i]],
                            changes_per_ind[i][next_change_ind[i]],
                            change_times[t], change_times[t+2])
                if parallel:
                    all_ll_diffs = world.gather(ll_diffs.sum(axis=0), 0)
                else:
                    all_ll_diffs = [ll_diffs.sum(axis=0)]
                if world_rank == 0:
                    total_ll_diffs = sum(all_ll_diffs)
                    total_ll_diffs[0] -= \
                            penalty_func(changes[change_times[t]]
                                    | changes[change_times[t+1]]) \
                            - penalty_func(changes[change_times[t]]) \
                            - penalty_func(changes[change_times[t+1]])
                    total_ll_diffs[-1] \
                            -= penalty_func(changes[change_times[t+2]]
                                    | changes[change_times[t+1]]) \
                            - penalty_func(changes[change_times[t+2]]) \
                            - penalty_func(changes[change_times[t+1]])
                    max_t = int(np.argmax(total_ll_diffs) + change_times[t])
                else:
                    max_t = None
                if parallel:
                    max_t = world.bcast(max_t, 0)
                if max_t != change_times[t+1]:
                    if max_t == change_times[t] or max_t == change_times[t+2]:
                        for i, ind in enumerate(inds):
                            if ind in changes[change_times[t+1]]:
                                if ind in changes[max_t]:
                                    changes_per_ind[i].pop(prev_change_ind[i]+1)
                                    next_change_ind[i] -= 1
                                else:
                                    changes_per_ind[i][prev_change_ind[i]+1] \
                                            = max_t
                        changes[max_t] |= changes.pop(change_times[t+1])
                        change_times.pop(t+1)
                        t -= 1
                    else:
                        changes[max_t] = changes.pop(change_times[t+1])
                        change_times[t+1] = max_t
                        for i, ind in enumerate(inds):
                            if ind in changes[max_t]:
                                changes_per_ind[i][prev_change_ind[i]+1] = max_t
                t += 1
        prev_nchange_times = len(changes)
        changes.pop(0)
        changes.pop(T)

        if verbose and world_rank == 0:
            count = sum([len(changes[t]) for t in changes])
            _s = lambda _x: '' if _x == 1 else 's'
            print 'Iteration %d done, %d change time%s, %d change%s' % (iter,
                    len(changes), _s(len(changes)), count, _s(count))
        if world_rank == 0:
            change_history.append(changes)
            finished = False
            if len(changes) == 0:
                finished = True
            if iter > 0:
                for old_changes in change_history[:-1]:
                    if changes == old_changes:
                        finished = True
        else:
            finished = None
        if parallel:
            finished = world.bcast(finished, 0)
        if finished:
            break

        if verbose and world_rank == 0:
            print 'Starting iteration ' + str(iter+1)
            print '...updating penalties'

        # Update penalties using new changes
        changes_mat = scipy.sparse.lil_matrix((J, len(changes)), dtype=group_dtype)
        change_times = changes.keys()
        change_times.sort()
        change_times = np.array(change_times)
        for i, t in enumerate(change_times):
            changes_mat[list(changes[t]), i] = 1
        changes_mat = changes_mat.tocsc()
        try:
            totals = groups_mat.dot(changes_mat)
        except MemoryError:
            print 'Memory error in multiplication: ' + str(groups_mat.shape) \
                    + ', ' + str(changes_mat.shape)
            raise
        if world_rank == 0:
            dense_totals = totals.toarray()
            current = (dense_totals**beta).sum(axis=0)
        else:
            current = None
        if parallel:
            current = world.bcast(current, 0)
        # Reset penalties to the values they would take if there were no changes
        if len(inds) > 0:
            for i, ind in enumerate(inds):
                if not disabled[i]:
                    penalties[i] = lam * (len(group_inds[i]))**alpha * \
                            rands[i] / 0.9
            cmat = np.asarray(changes_mat[inds,:].todense(), dtype='bool')
            for i, ind in enumerate(inds):
                if not disabled[i]:
                    submat = totals[group_inds[i],:].toarray()
                    cup = current + ((submat+1)**beta - submat**beta).sum(axis=0)
                    cdown = current + (np.maximum(submat-1,0)**beta
                            - submat**beta).sum(axis=0)
                    cdown = np.maximum(cdown, 0)
                    penalties[i, change_times - 1] = \
                            lam * ((1-cmat[i]) * (cup**alpha - current**alpha) \
                            + cmat[i] * (current**alpha - cdown**alpha))

    if verbose and world_rank == 0:
        print 'Iterations complete'
    return dict(changes)
