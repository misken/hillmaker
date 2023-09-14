"""
The :mod:`hillmaker.summarize` module includes functions for computing occupancy,
arrival, and departure statistics by time bin of day, day of week and one
or more category fields.
"""

# Copyright 2022 Mark Isken

import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from pandas.core.groupby import DataFrameGroupBy
from pandas import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns

from hillmaker.hmlib import pctile_field_name

# This should inherit level from root logger
logger = logging.getLogger(__name__)


def summarize(bydt_dfs: Dict,
              percentiles: Tuple[float] | List[float] = (0.25, 0.5, 0.75, 0.95, 0.99),
              nonstationary_stats: bool = True, stationary_stats: bool = True, verbosity: int = 0):
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
        If true, overall, non-time bin dependent, stats are computed. Else, they aren't computed. Default is True

    verbosity : int, optional
        The verbosity level. The default, zero, means silent mode. Higher numbers mean more output messages.


    Returns
    -------
    Dict of DataFrames
       Occupancy, arrival and departure summaries as DataFrames

    Examples
    --------

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
            summaries = summarize_nonstationary(bydt_df, catfield, percentiles, verbosity)
            summary_nonstationary_dfs[summary_key] = summaries

    summary_stationary_dfs = {}

    if stationary_stats:
        for bydt, bydt_df in bydt_dfs.items():
            midx_fields = bydt_df.index.names
            catfield = [x for x in midx_fields if x != 'datetime']
            summary_key = '_'.join(catfield)
            summaries = summarize_stationary(bydt_df, catfield, percentiles)
            summary_stationary_dfs[summary_key] = summaries

    summaries_all = {'nonstationary': summary_nonstationary_dfs, 'stationary': summary_stationary_dfs}

    return summaries_all


def summarize_nonstationary(bydt_df: pd.DataFrame, catfield: str | List[str] = None,
                            percentiles: Tuple[float] | List[float] = (0.25, 0.5, 0.75, 0.95, 0.99),
                            verbosity: int = 0):
    """
    Compute summary statistics by category by time bin of day by day of week

    Parameters
    ----------

    bydt_df : DataFrame
       Occupancy, arrivals, departures by category (optional) and by datetime bin

    catfield : str, optional
        Column name corresponding to the categories. If none is specified, then only overall occupancy is analyzed.

    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)

    verbosity : int, optional
        The verbosity level. The default, zero, means silent mode. Higher numbers mean more output messages.

    Returns
    -------
    tuple of DataFrames
       Occupancy, arrival and departure summaries as DataFrames

    Examples
    --------

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
            bydt_dfgrp = bydt_df.groupby(['day_of_week', 'dow_name', 'bin_of_day', 'bin_of_day_str'])
        else:
            bydt_dfgrp = bydt_df.groupby([*catfield, 'day_of_week', 'dow_name', 'bin_of_day', 'bin_of_day_str'])
    else:
        bydt_dfgrp = bydt_df.groupby(['day_of_week', 'dow_name', 'bin_of_day', 'bin_of_day_str'])

    if verbosity > 1:
        print(bydt_df.head())

    occ_stats = bydt_dfgrp['occupancy'].apply(summary_stats, percentiles)
    arr_stats = bydt_dfgrp['arrivals'].apply(summary_stats, percentiles)
    dep_stats = bydt_dfgrp['departures'].apply(summary_stats, percentiles)

    if verbosity > 1:
        print(occ_stats.head())

    occ_stats_summary = occ_stats.unstack()
    arr_stats_summary = arr_stats.unstack()
    dep_stats_summary = dep_stats.unstack()

    if verbosity > 1:
        print(occ_stats_summary.head())

    summaries = {'occupancy': occ_stats_summary, 'arrivals': arr_stats_summary,
                 'departures': dep_stats_summary}

    logger.info(f'Created nonstationary summaries - {catfield}')

    return summaries


def summarize_stationary(bydt_df: pd.DataFrame, catfield: str | List[str] = None,
                         percentiles: Tuple[float] | List[float] = (0.25, 0.5, 0.75, 0.95, 0.99)):
    """
    Compute summary statistics by category (no time of day or day of week)

    Parameters
    ----------
    bydt_df: DataFrames
       Occupancy, arrivals, departures by category(ies) by datetime bin

    catfield : str, optional
       Column name corresponding to the categories. If none is specified,
       then only overall occupancy is analyzed.

    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)


    Returns
    -------
    tuple of DataFrames
       Occupancy, arrival and departure summaries as DataFrames

    Examples
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

    logger.info(f'Created stationary summaries - {catfield}')

    return summaries


def summary_stats(group: DataFrameGroupBy,
                  percentiles: Tuple[float] | List[float] = (0.25, 0.5, 0.75, 0.95, 0.99),
                  ):
    """
    Compute summary statistics on a pandas `DataFrameGroupBy` object.

    Parameters
    ----------
    group : pd.DataFrameGroupBy
        The grouping is by category
    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)

    Returns
    -------
    Dict whose keys are '{stub}_{statistic}'. Dict values are `DataFrame` objects.

    """
    stats = {'count': group.count(), 'mean': group.mean(),
             'min': group.min(),
             'max': group.max(), 'stdev': group.std(), 'sem': group.sem(),
             'var': group.var(), 'cv': group.std() / group.mean() if group.mean() > 0 else 0,
             'skew': group.skew(), 'kurt': group.kurt()}

    if percentiles is not None:
        pctile_vals = group.quantile(percentiles)

        for p in percentiles:
            pctile_name = pctile_field_name(p)
            stats[pctile_name] = pctile_vals[p]

    return stats


def summarize_los(stops_preprocessed_df: DataFrame, cat_field: str, los_field: str) -> Dict:
    """
    Summarize length of stay.

    Creates tabular summaries along with histograms.

    Parameters
    ----------
    stops_preprocessed_df : DataFrame

    cat_field : str
        Column name for the category values.

    los_field : str
        Column name for the length of stay values.

    Returns
    -------
    dict

    """

    # Create tabular summaries
    cat_field_grp = stops_preprocessed_df.groupby([cat_field])
    los_bycat_stats = cat_field_grp[los_field].apply(summary_stats).unstack()
    all_grp = stops_preprocessed_df.groupby(by = lambda x: 'all')
    los_stats = all_grp[los_field].apply(summary_stats).unstack()

    cols = ['count', 'mean', 'min', 'max', 'stdev', 'cv', 'skew', 'p50', 'p75', 'p95', 'p99']
    float_format = '{0:.1f}'
    fmt_map = {'count': '{:.0f}',
               'mean': float_format,
               'min': float_format,
               'max': float_format,
               'stdev': float_format,
               'cv': float_format,
               'skew': float_format,
               'p50': float_format,
               'p75': float_format,
               'p95': float_format,
               'p99': float_format}

    los_bycat_stats_styled = los_bycat_stats[cols].style.format(fmt_map)
    los_stats_styled = los_stats[cols].style.format(fmt_map)

    # Create los plot
    g = sns.FacetGrid(data=stops_preprocessed_df, col=cat_field, sharex=False, sharey=False, col_wrap=3)
    plot = g.map(sns.histplot, los_field)
    plt.close() # Supress plot showing up in notebook

    results = {'los_bycat_stats': los_bycat_stats_styled,
               'los_stats': los_stats_styled,
               'los_histos': plot.fig}

    return results


if __name__ == '__main__':
    pass
