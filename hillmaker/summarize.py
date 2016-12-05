"""
The :mod:`hillmaker.summarize` module includes functions for computing occupancy,
arrival, and departure statistics by time bin of day and day of week.
"""

# Copyright 2015 Mark Isken
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

def summarize(bydt_dfs, nonstationary_stats=True, stationary_stats=True):
    """
    Compute summary statistics. Calls specific procedures for stationary and nonstationary stats.

    Parameters
    ----------
    bydt_dfs : Dict of DataFrames
       Occupancy, arrivals, departures by category by datetime bin. Usually computed by make_bydatetime.

    nonstationary_stats : bool, optional
       If true, datetime bin stats are computed. Else, they aren't computed. Default is True

    stationary_stats : bool, optional
       If true, overall, non time bin dependent, stats are computed. Else, they aren't computed. Default is True


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

        for bydt in bydt_dfs:


            bydt_df = bydt_dfs[bydt]
            catfieldplus = bydt_df.index.names
            catfield = [x for x in catfieldplus if x is not 'datetime']

            summary_key_list = catfield.copy()
            summary_key_list.append('dow')
            summary_key_list.append('binofday')

            summary_key = '_'.join(summary_key_list)

            summaries = summarize_nonstationary(bydt_df, catfield)

            summary_nonstationary_dfs[summary_key] = summaries

    summary_stationary_dfs = {}
    if stationary_stats:

        for bydt in bydt_dfs:

            bydt_df = bydt_dfs[bydt]

            catfieldplus = bydt_df.index.names
            catfield = [x for x in catfieldplus if x is not 'datetime']

            summary_key = '_'.join(catfield)

            summaries = summarize_stationary(bydt_df, catfield)

            summary_stationary_dfs[summary_key] = summaries

    summaries_all = {}
    summaries_all['nonstationary'] = summary_nonstationary_dfs
    summaries_all['stationary'] = summary_stationary_dfs

    return summaries_all

def summarize_nonstationary(bydt_df, catfield=None):
    """
    Compute summary statistics by category by time bin of day by day of week

    Parameters
    ----------
    bydt_df : DataFrame
       Occupancy, arrivals, departures by category (optional) and by datetime bin

    catfield : string or List of strings, optional
        Column name(s) corresponding to the categories. If none is specified, then only overall occupancy is analyzed.


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
        if catfield == []:
            bydt_dfgrp = bydt_df.groupby(['day_of_week', 'bin_of_day'])
        else:
            bydt_dfgrp = bydt_df.groupby([*catfield, 'day_of_week', 'bin_of_day'])
    else:
        bydt_dfgrp = bydt_df.groupby(['day_of_week', 'bin_of_day'])

    print(bydt_df.head())

    occ_stats = bydt_dfgrp['occupancy'].apply(summary_stats)
    arr_stats = bydt_dfgrp['arrivals'].apply(summary_stats)
    dep_stats = bydt_dfgrp['departures'].apply(summary_stats)

    print(occ_stats.head())

    occ_stats_summary = occ_stats.unstack()
    arr_stats_summary = arr_stats.unstack()
    dep_stats_summary = dep_stats.unstack()

    print(occ_stats_summary.head())

    summaries = {}
    summaries['occupancy'] = occ_stats_summary
    summaries['arrivals'] = arr_stats_summary
    summaries['departures'] = dep_stats_summary

    return summaries


def summarize_stationary(bydt_df, catfield=None):
    """
    Compute summary statistics by category (no time of day or day of week)

    Parameters
    ----------
    bydt_df: DataFrames
       Occupancy, arrivals, departures by category(ies) by datetime bin

    catfield : string or List of strings, optional
       Column name(s) corresponding to the categories. If none is specified, then only overall occupancy is analyzed.

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
        if catfield == []:
            fake_key = np.full(len(bydt_df['datetime']), 1)
            bydt_dfgrp = bydt_df.groupby(fake_key)

        else:
            bydt_dfgrp = bydt_df.groupby([*catfield])
    else:
        fake_key = np.full(len(bydt_df['datetime']), 1)
        bydt_dfgrp = bydt_df.groupby(fake_key)


    occ_stats = bydt_dfgrp['occupancy'].apply(summary_stats)
    arr_stats = bydt_dfgrp['arrivals'].apply(summary_stats)
    dep_stats = bydt_dfgrp['departures'].apply(summary_stats)

    occ_stats_summary = occ_stats.unstack()
    arr_stats_summary = arr_stats.unstack()
    dep_stats_summary = dep_stats.unstack()

    summaries = {}
    summaries['occupancy'] = occ_stats_summary
    summaries['arrivals'] = arr_stats_summary
    summaries['departures'] = dep_stats_summary

    return summaries


def summary_stats(group, stub=''):
        return {stub+'count': group.count(), stub+'mean': group.mean(),
                stub+'min': group.min(),
                stub+'max': group.max(), 'stdev': group.std(), 'sem': group.sem(),
                stub+'var': group.var(), 'cv': group.std() / group.mean() if group.mean() > 0 else 0,
                stub+'skew': group.skew(), 'kurt': group.kurt(),
                stub+'p50': group.quantile(0.5), stub+'p55': group.quantile(0.55),
                stub+'p60': group.quantile(0.6), stub+'p65': group.quantile(0.65),
                stub+'p70': group.quantile(0.7), stub+'p75': group.quantile(0.75),
                stub+'p80': group.quantile(0.8), stub+'p85': group.quantile(0.85),
                stub+'p90': group.quantile(0.9), stub+'p95': group.quantile(0.95),
                stub+'p975': group.quantile(0.975),
                stub+'p99': group.quantile(0.99)}

if __name__ == '__main__':

    pass

