"""
The :mod:`hillmaker.summarize` module includes functions for computing occupancy,
arrival, and departure statistics by time bin of day and day of week.
"""

# Authors: Mark Isken <isken@oakland.edu>
# License: BSD 3 clause

import pandas as pd


def summarize_bydatetime(bydt_df):
    """
    Compute summary statistics by category by time bin of day by day of week

    Parameters
    ----------
    bydt_df : DataFrame
       Occupancy, arrivals, departures by category by datetime bin

    Returns
    -------
    tuple of DataFrame
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

    bydt_dfgrp = bydt_df.groupby(['category', 'day_of_week', 'bin_of_day'])

    occ_stats = bydt_dfgrp['occupancy'].apply(summary_stats)
    arr_stats = bydt_dfgrp['arrivals'].apply(summary_stats)
    dep_stats = bydt_dfgrp['departures'].apply(summary_stats)

    occ_stats_summary = occ_stats.unstack()
    arr_stats_summary = arr_stats.unstack()
    dep_stats_summary = dep_stats.unstack()

    return occ_stats_summary, arr_stats_summary, dep_stats_summary


def summarize_bycategory(bydt_df):
    """
    Compute summary statistics by category (no time of day or day of week)

    Parameters
    ----------
    bydt_df: DataFrame
       Occupancy, arrivals, departures by category by datetime bin

    Returns
    -------
    tuple of DataFrame
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

    bydt_dfgrp = bydt_df.groupby(['category'])

    occ_stats = bydt_dfgrp['occupancy'].apply(summary_stats)
    arr_stats = bydt_dfgrp['arrivals'].apply(summary_stats)
    dep_stats = bydt_dfgrp['departures'].apply(summary_stats)

    occ_stats_summary = occ_stats.unstack()
    arr_stats_summary = arr_stats.unstack()
    dep_stats_summary = dep_stats.unstack()

    return occ_stats_summary, arr_stats_summary, dep_stats_summary


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

    scenario_name = 'log_unitocc_test'
    file_bydt_csv = 'testing/bydatetime_' + scenario_name + '.csv'

    unitocc_bydt = pd.read_csv(file_bydt_csv)

    occ, arr, dep = summarize_bydatetime(unitocc_bydt)

    file_occ_csv = 'testing/occ_stats_summary_' + scenario_name + '.csv'
    file_arr_csv = 'testing/arr_stats_summary_' + scenario_name + '.csv'
    file_dep_csv = 'testing/dep_stats_summary_' + scenario_name + '.csv'

    occ.to_csv(file_occ_csv)
    arr.to_csv(file_arr_csv)
    dep.to_csv(file_dep_csv)