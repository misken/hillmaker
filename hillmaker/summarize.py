"""
The :mod:`hillmaker.summarize` module includes functions for computing occupancy,
arrival, and departure statistics by time bin of day, day of week and one
or more category fields.
"""

# Copyright 2015, 2020 Mark Isken
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd
import numpy as np


def summarize(bydt_dfs, percentiles=(0.25, 0.5, 0.75, 0.95, 0.99),
              nonstationary_stats=True, stationary_stats=True, totals=1, verbose=0):
    """
    Compute summary statistics. Calls specific procedures for stationary and nonstationary stats.

    Parameters
    ----------
    bydt_dfs : Dict of DataFrames
        Occupancy, arrivals, departures by category by datetime bin. Usually computed by make_bydatetime.

    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)

    nonstationary_stats : bool, optional
        If true, datetime bin stats are computed. Else, they aren't computed. Default is True

    stationary_stats : bool, optional
        If true, overall, non time bin dependent, stats are computed. Else, they aren't computed. Default is True

    verbose : int, optional
        The verbosity level. The default, zero, means silent mode. Higher numbers mean more output messages.


    Returns
    -------
    Dict of DataFrames
       Occupancy, arrival and departure summaries as DataFrames

    Examples
    --------

    TODO
    ----

    Notes
    -----

    References
    ----------

    See Also
    --------
    """

# Store main results bydatetime DataFrame

    summary_nonstationary_dfs = {}
    if nonstationary_stats:

        for bydt, bydt_df in bydt_dfs.items():

            midx_fields = bydt_df.index.names
            catfield = [x for x in midx_fields if x != 'datetime']

            summary_key_list = catfield.copy()
            summary_key_list.append('dow')
            summary_key_list.append('binofday')

            summary_key = '_'.join(summary_key_list)
            summaries = summarize_nonstationary(bydt_df, catfield, percentiles, verbose)
            summary_nonstationary_dfs[summary_key] = summaries

    summary_stationary_dfs = {}

    if stationary_stats:

        for bydt in bydt_dfs:

            bydt_df = bydt_dfs[bydt]

            midx_fields = bydt_df.index.names
            catfield = [x for x in midx_fields if x != 'datetime']

            summary_key = '_'.join(catfield)

            summaries = summarize_stationary(bydt_df, catfield, percentiles, verbose)

            summary_stationary_dfs[summary_key] = summaries

    summaries_all = {'nonstationary': summary_nonstationary_dfs, 'stationary': summary_stationary_dfs}

    return summaries_all


def summarize_nonstationary(bydt_df, catfield=None,
                            percentiles=(0.25, 0.5, 0.75, 0.95, 0.99), verbose=0):
    """
    Compute summary statistics by category by time bin of day by day of week

    Parameters
    ----------

    bydt_df : DataFrame
       Occupancy, arrivals, departures by category (optional) and by datetime bin

    catfield : string or List of strings, optional
        Column name(s) corresponding to the categories. If none is specified, then only overall occupancy is analyzed.

    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)

    verbose : int, optional
        The verbosity level. The default, zero, means silent mode. Higher numbers mean more output messages.

    Returns
    -------
    tuple of DataFrames
       Occupancy, arrival and departure summaries as DataFrames

    Examples
    --------

    TODO
    ----

    Notes
    -----

    References
    ----------

    See Also
    --------
    """

    if catfield is not None:
        if isinstance(catfield, str):
            catfield = [catfield]
        if not catfield:
            bydt_dfgrp = bydt_df.groupby(['day_of_week', 'dow_name', 'bin_of_day'])
        else:
            bydt_dfgrp = bydt_df.groupby([*catfield, 'day_of_week', 'dow_name', 'bin_of_day'])
    else:
        bydt_dfgrp = bydt_df.groupby(['day_of_week', 'dow_name', 'bin_of_day'])

    if verbose > 1:
        print(bydt_df.head())

    occ_stats = bydt_dfgrp['occupancy'].apply(summary_stats, percentiles)
    arr_stats = bydt_dfgrp['arrivals'].apply(summary_stats, percentiles)
    dep_stats = bydt_dfgrp['departures'].apply(summary_stats, percentiles)

    if verbose > 1:
        print(occ_stats.head())

    occ_stats_summary = occ_stats.unstack()
    arr_stats_summary = arr_stats.unstack()
    dep_stats_summary = dep_stats.unstack()

    if verbose > 1:
        print(occ_stats_summary.head())

    summaries = {'occupancy': occ_stats_summary, 'arrivals': arr_stats_summary,
                 'departures': dep_stats_summary}

    if verbose:
        print('Created nonstationary summaries - {}'.format(catfield))

    return summaries


def summarize_stationary(bydt_df, catfield=None,
                         percentiles=(0.25, 0.5, 0.75, 0.95, 0.99), verbose=0):
    """
    Compute summary statistics by category (no time of day or day of week)

    Parameters
    ----------
    bydt_df: DataFrames
       Occupancy, arrivals, departures by category(ies) by datetime bin

    catfield : string or List of strings, optional
       Column name(s) corresponding to the categories. If none is specified,
       then only overall occupancy is analyzed.

    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)

    verbose : int, optional
        The verbosity level. The default, zero, means silent mode.
        Higher numbers mean more output messages.

    Returns
    -------
    tuple of DataFrames
       Occupancy, arrival and departure summaries as DataFrames

    Examples
    --------

    TODO
    ----

    Notes
    -----

    References
    ----------

    See Also
    --------
    """

    if catfield is not None:
        if isinstance(catfield, str):
            catfield = [catfield]
        if not catfield:
            fake_key = np.full(len(bydt_df.index), 1)
            bydt_dfgrp = bydt_df.groupby(fake_key)
        else:
            bydt_dfgrp = bydt_df.groupby([*catfield])
    else:
        fake_key = np.full(len(bydt_df.index), 1)
        bydt_dfgrp = bydt_df.groupby(fake_key)

    occ_stats = bydt_dfgrp['occupancy'].apply(summary_stats, percentiles)
    arr_stats = bydt_dfgrp['arrivals'].apply(summary_stats, percentiles)
    dep_stats = bydt_dfgrp['departures'].apply(summary_stats, percentiles)

    occ_stats_summary = occ_stats.unstack()
    arr_stats_summary = arr_stats.unstack()
    dep_stats_summary = dep_stats.unstack()

    summaries = {'occupancy': occ_stats_summary, 'arrivals': arr_stats_summary,
                 'departures': dep_stats_summary}

    if verbose:
        print('Created stationary summaries - {}'.format(catfield))

    return summaries


def summary_stats(group, percentiles=(0.25, 0.5, 0.75, 0.95, 0.99), stub=''):
    stats = {stub+'count': group.count(), stub+'mean': group.mean(),
                stub+'min': group.min(),
                stub+'max': group.max(), 'stdev': group.std(), 'sem': group.sem(),
                stub+'var': group.var(), 'cv': group.std() / group.mean() if group.mean() > 0 else 0,
                stub+'skew': group.skew(), 'kurt': group.kurt()}

    if percentiles is not None:
        pctile_vals = group.quantile(percentiles)

        for p in percentiles:
            pctile_name = '{}p{:d}'.format(stub, int(100 * p))
            stats[pctile_name] = pctile_vals[p]

    return stats


if __name__ == '__main__':

    pass

