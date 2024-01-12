"""
The :mod:`hillmaker.bydatetime` module includes functions for computing occupancy,
arrival, and departures by time bin of day and date.
"""

# Copyright 2022-2023 Mark Isken

import logging
from typing import List

import numpy as np
import pandas as pd
from pandas import DataFrame
from pandas import Series
from pandas import Timestamp
from pandas.tseries.offsets import Minute

import hillmaker.hmlib as hmlib

CONST_FAKE_OCCWEIGHT_FIELDNAME = 'FakeOccWeightField'
CONST_FAKE_CATFIELD_NAME = 'FakeCatForTotals'
TOTAL_STR = 'total'
OCC_TOLERANCE = 0.02
EARLY_START_ANALYSIS_TOLERANCE = 48.0
LATE_END_ANALYSIS_TOLERANCE = 48.0

# This should inherit level from root logger
logger = logging.getLogger(__name__)


def make_bydatetime(stops_df: pd.DataFrame, infield: str, outfield: str,
                    start_analysis_np: np.datetime64 | Timestamp,
                    end_analysis_np: np.datetime64 | Timestamp,
                    cat_field: str | List[str] = None,
                    bin_size_minutes: int = 60,
                    cat_to_exclude: List[str] = None,
                    occ_weight_field: str = None,
                    edge_bins: int = 1,
                    highres_bin_size_minutes: int = 5,
                    keep_highres_bydatetime: bool = False,
                    ):
    """
    Create bydatetime table from which summary statistics can be computed.

    Parameters
    ----------
    stops_df: DataFrame
        Each row is an entity representing a stop (an event with an arrival and departure time)

    infield: str
        Name of column in stops_df to use as arrival datetime

    outfield: str
        Name of column in stops_df to use as departure datetime

    start_analysis_np: numpy datetime64[ns]
        Start date for the analysis

    end_analysis_np: numpy datetime64[ns]
        End date for the analysis

    cat_field : str, optional
        Column name corresponding to the categories.
        If none is specified, then only overall occupancy is analyzed.

    bin_size_minutes: int, default=60
        Bin size in minutes. Should divide evenly into 1440.

    cat_to_exclude: list of str, default=None
        Categories to ignore

    occ_weight_field : str, optional
        Column name corresponding to the weights to use for occupancy incrementing.
        If omitted, occupancy weights of 1.0 are used (i.e. pure occupancy)

    edge_bins: int, default=1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=whole bin

    highres_bin_size_minutes: int, default=5
        Resolution bin size in minutes. Should divide evenly into 1440 and be <= `bin_size_mins`.

    keep_highres_bydatetime : bool, optional
        Save the high resolution bydatetime dataframe in hills attribute. Default is False.

    Returns
    -------
    Dict of DataFrames
       Occupancy, arrivals, departures by category by datetime bin

    Examples
    --------
    bydt_dfs = make_bydatetime(stops_df, 'InTime', 'OutTime',
    ...                        datetime(2014, 3, 1), datetime(2014, 6, 30), 'PatientType', 60)

    """
    # Number of bins in analysis span
    num_bins = hmlib.bin_of_analysis_range(end_analysis_np, start_analysis_np, highres_bin_size_minutes) + 1

    # Compute min and max of in and out times
    min_intime = stops_df[infield].min()
    max_intime = stops_df[infield].max()
    min_outtime = stops_df[outfield].min()
    max_outtime = stops_df[outfield].max()

    logger.debug(f"min of intime: {min_intime}")
    logger.debug(f"max of intime: {max_intime}")
    logger.debug(f"min of outtime: {min_outtime}")
    logger.debug(f"max of outtime: {max_outtime}")

    # Check for mismatch between analysis dates and dates in stops_df
    check_date_ranges(start_analysis_np, end_analysis_np, min_intime, max_outtime)
    logger.debug(
        f'start analysis: {np.datetime_as_string(start_analysis_np, unit="D")}, end analysis: {np.datetime_as_string(end_analysis_np, unit="D")}')

    # Occupancy weights
    # If no occ weight field specified, create fake one containing 1.0 as values.
    # Avoids having to check during dataframe iteration whether to use
    # default occupancy weight.
    if occ_weight_field is None:
        occ_weight_vec = np.ones(len(stops_df.index), dtype=np.float64)
        occ_weight_df = DataFrame({CONST_FAKE_OCCWEIGHT_FIELDNAME: occ_weight_vec})
        stops_df = pd.concat([stops_df, occ_weight_df], axis=1)
        occ_weight_field = CONST_FAKE_OCCWEIGHT_FIELDNAME

    # Handle cases of no catfield, or a single fieldname, (no longer supporting a list of fieldnames)
    # If no category, add a temporary dummy column populated with a totals str

    # do_totals = True
    if cat_field is not None:
        has_cat_field = True
        # If catfield a string, convert to list
        # Keeping catfield as a list in case I change mind about multiple category fields
        if isinstance(cat_field, str):
            cat_field = [cat_field]
    else:
        # No category field, create fake category field containing a single value
        has_cat_field = False
        tot_list = [TOTAL_STR] * len(stops_df)
        tot_series = Series(tot_list, dtype=str, name=CONST_FAKE_CATFIELD_NAME)
        tot_field_df = DataFrame({CONST_FAKE_CATFIELD_NAME: tot_series})
        stops_df = pd.concat([stops_df, tot_field_df], axis=1)
        cat_field = [CONST_FAKE_CATFIELD_NAME]
        # do_totals = False

    # Get the unique category values and exclude any specified to exclude
    categories = []
    if isinstance(cat_to_exclude, str):
        cat_to_exclude = [cat_to_exclude]

    if cat_to_exclude is not None and len(cat_to_exclude) > 0:
        for i in range(len(cat_field)):
            categories.append(tuple([c for c in stops_df[cat_field[i]].unique() if c not in cat_to_exclude]))
    else:
        for i in range(len(cat_field)):
            categories.append(tuple([c for c in stops_df[cat_field[i]].unique()]))

    for i in range(len(cat_field)):
        stops_df = stops_df[stops_df[cat_field[i]].isin(categories[i])]

    # TEMPORARY ASSUMPTION - only a single category field is allowed
    # Main loop over the categories. Filter stops_df by category and then do
    # numpy based occupancy computations.
    results = {}
    for cat in categories[0]:
        cat_df = stops_df[stops_df[cat_field[0]] == cat]
        num_stop_recs = len(cat_df)

        # Convert Series to numpy arrays for infield, outfield, occ_weight
        in_ts_np = cat_df[infield].to_numpy()
        out_ts_np = cat_df[outfield].to_numpy()
        occ_weight = cat_df[occ_weight_field].to_numpy()

        # Compute entry and exit bin arrays
        entry_bin = hmlib.bin_of_analysis_range(in_ts_np, start_analysis_np, highres_bin_size_minutes)
        logger.debug(f'min of entry time_bin = {np.amin(entry_bin)}')
        exit_bin = hmlib.bin_of_analysis_range(out_ts_np, start_analysis_np, highres_bin_size_minutes)
        logger.debug(f'max of exit time_bin = {np.amax(exit_bin)} and num_bins={num_bins}')

        # Compute inbin and outbin fraction arrays
        entry_bin_frac = in_bin_occ_frac(entry_bin, in_ts_np, out_ts_np,
                                         start_analysis_np, highres_bin_size_minutes, edge_bins=edge_bins)
        exit_bin_frac = out_bin_occ_frac(exit_bin, in_ts_np, out_ts_np,
                                         start_analysis_np, highres_bin_size_minutes, edge_bins=edge_bins)

        # Create list of occupancy incrementer arrays
        list_of_inc_arrays = [make_occ_inc(entry_bin[i], exit_bin[i],
                                           entry_bin_frac[i], exit_bin_frac[i],
                                           occ_weight[i]) for i in range(num_stop_recs)]

        # Create array of stop record types
        rec_type = cat_df.apply(lambda x:
                                hmlib.stoprec_relationship_type(x[infield], x[outfield],
                                                                start_analysis_np, end_analysis_np), axis=1).to_numpy()

        # Do the occupancy incrementing
        rec_counts = update_occ_incs(entry_bin, exit_bin, list_of_inc_arrays, rec_type, num_bins)
        logger.debug(f'cat {cat} {rec_counts}')

        occ = np.zeros(num_bins, dtype=np.float64)
        update_occ(occ, entry_bin, rec_type, list_of_inc_arrays)

        # Count unadjusted arrivals and departures by bin
        arr = np.bincount(entry_bin, minlength=num_bins).astype(np.float64)
        dep = np.bincount(exit_bin, minlength=num_bins).astype(np.float64)

        # Adjust the arrival and departure counts to account for rec_types left, right, and outer
        arr[0] -= rec_counts.get('left', 0)
        arr[0] -= rec_counts.get('outer', 0)
        dep[num_bins - 1] -= rec_counts.get('right', 0)
        dep[num_bins - 1] -= rec_counts.get('outer', 0)

        # Combine arr, dep, occ (in that order) into matrix
        arr_dep_occ = np.column_stack((arr, dep, occ))

        # Conservation of flow checks for num arrivals and departures
        num_arrivals_hm = arr.sum()
        num_departures_hm = dep.sum()

        num_arrivals_stops = cat_df.loc[(cat_df[infield] >= start_analysis_np) &
                                        (cat_df[infield] <= end_analysis_np)].index.size

        num_departures_stops = cat_df.loc[(cat_df[outfield] >= start_analysis_np) &
                                          (cat_df[outfield] <= end_analysis_np)].index.size

        logger.debug(f'cat {cat} num_arrivals_hm {num_arrivals_hm:.0f} num_arrivals_stops {num_arrivals_stops}')
        logger.debug(
            f'cat {cat} num_departures_hm {num_departures_hm:.0f} num_departures_stops {num_departures_stops}')

        if num_arrivals_hm != num_arrivals_stops:
            logger.warning(
                f'num_arrivals_hm ({num_arrivals_hm:.0f}) not equal to num_arrivals_stops ({num_arrivals_stops})')

        if num_departures_hm != num_departures_stops:
            logger.warning(
                f'num_departures_hm ({num_departures_hm:.0f}) not equal to departures_stops ({num_departures_stops})')

        # Conservation of flow checks for weighted occupancy
        tot_occ_him = occ.sum()

        tot_occ_mins_stops = \
            (cat_df[occ_weight_field] * (cat_df[outfield] - cat_df[infield]).dt.total_seconds()).sum() / 60
        tot_occ_stops = tot_occ_mins_stops / highres_bin_size_minutes

        logger.debug(f'cat {cat} tot_occ_hm {tot_occ_him:.2f} tot_occ_stops {tot_occ_stops:.2f}')
        if (tot_occ_him - tot_occ_stops) / tot_occ_stops > OCC_TOLERANCE:
            logger.warning(
                f'cat {cat} Weighted occupancy differs by more than {OCC_TOLERANCE})')

        # Store results
        results[cat] = arr_dep_occ

    # Convert stacked arrays to Dataframes. Result is dict with keys 'agg' and 'res'
    bydt_dfs_cat = arrays_to_df(results, start_analysis_np, end_analysis_np,
                                bin_size_minutes, highres_bin_size_minutes, cat_field)

    # Store main results bydatetime DataFrames
    bydt_dfs = {}
    bydt_highres_dfs = {}

    if has_cat_field:
        cat_key = '_'.join(bydt_dfs_cat['agg'].index.names)
        bydt_dfs[cat_key] = bydt_dfs_cat['agg']
        if keep_highres_bydatetime:
            highres_cat_key = f'{cat_key}_highres'
            bydt_highres_dfs[highres_cat_key] = bydt_dfs_cat['highres']

    # Compute totals - doing this even if only a fake category field
    results_totals = {}
    totals_key = 'datetime'

    total_occ_arr_dep = np.zeros((num_bins, 3), dtype=np.float64)
    for cat, oad_array in results.items():
        total_occ_arr_dep += oad_array

    results_totals[totals_key] = total_occ_arr_dep
    bydt_dfs_total = arrays_to_df(results_totals, start_analysis_np, end_analysis_np,
                                  bin_size_minutes, highres_bin_size_minutes)
    bydt_dfs[totals_key] = bydt_dfs_total['agg']
    if keep_highres_bydatetime:
        highres_totals_key = f'{totals_key}_highres'
        bydt_highres_dfs[highres_totals_key] = bydt_dfs_total['highres']

    return bydt_dfs, bydt_highres_dfs


def check_date_ranges(start_analysis_dt, end_analysis_dt, min_in_date, max_out_date):
    """

    Parameters
    ----------
    start_analysis_dt
    end_analysis_dt
    min_in_date
    max_out_date

    Returns
    -------

    """

    start_analysis_early_hrs = (min_in_date - start_analysis_dt) / pd.Timedelta(1, unit="h")
    end_analysis_late_hrs = (end_analysis_dt - max_out_date) / pd.Timedelta(1, unit="h")

    if start_analysis_early_hrs > EARLY_START_ANALYSIS_TOLERANCE:
        logger.warning(f'Analysis starts {start_analysis_early_hrs:.2f} hours before first arrival')

    if end_analysis_late_hrs > LATE_END_ANALYSIS_TOLERANCE:
        logger.warning(f'Analysis ends {end_analysis_late_hrs:.2f} hours after last departure')


def arrays_to_df(results_arrays, start_analysis_dt, end_analysis_dt,
                 bin_size_minutes, resolution_bin_size_minutes,
                 catfield=None):
    """
    Converts results dict from ndarrays to Dataframes

    results_arrays: dict of ndarrays
    """

    rng_bydt = Series(pd.date_range(start_analysis_dt, end_analysis_dt, freq=Minute(resolution_bin_size_minutes)))

    agg_dfs = []
    res_dfs = []
    for cat, ado_array in results_arrays.items():
        # Create Dataframe from ndarray
        res_df = pd.DataFrame(ado_array, columns=['arrivals', 'departures', 'occupancy'])

        # Add datetime column and category column (still assuming just one category field)
        res_df['datetime'] = rng_bydt
        res_df['date'] = res_df['datetime'].map(lambda x: x.date())
        res_df['bin_of_day'] = res_df['datetime'].map(lambda x: hmlib.bin_of_day(x, bin_size_minutes))

        # Aggregate by bin_size_minutes if necessary

        if catfield:
            for c in catfield:
                res_df[c] = cat

            agg_df = res_df.groupby([catfield[0], 'date', 'bin_of_day']).agg(
                arrivals=pd.NamedAgg(column='arrivals', aggfunc='sum'),
                departures=pd.NamedAgg(column='departures', aggfunc='sum'),
                occupancy=pd.NamedAgg(column='occupancy', aggfunc='mean'))
        else:
            agg_df = res_df.groupby(['date', 'bin_of_day']).agg(
                arrivals=pd.NamedAgg(column='arrivals', aggfunc='sum'),
                departures=pd.NamedAgg(column='departures', aggfunc='sum'),
                occupancy=pd.NamedAgg(column='occupancy', aggfunc='mean'))

        agg_df = agg_df.reset_index(drop=False)

        # Compute datetime
        agg_df['datetime'] = agg_df.apply(
            lambda x: pd.Timestamp(x.date) + pd.Timedelta(x.bin_of_day * bin_size_minutes, 'm'), axis=1)

        # Add additional fields
        agg_df['day_of_week'] = agg_df['datetime'].map(lambda x: x.weekday())
        agg_df['dow_name'] = agg_df['datetime'].map(lambda x: x.strftime('%a'))
        agg_df['bin_of_day_str'] = agg_df['datetime'].map(lambda x: x.strftime('%H:%M'))
        agg_df['bin_of_week'] = agg_df['datetime'].map(lambda x: hmlib.bin_of_week(x, bin_size_minutes))

        agg_dfs.append(agg_df)  # Add category specific dataframe to list
        res_dfs.append(res_df)  # Add category specific dataframe to list

    # Concatenate the dfs in cat_dfs
    if len(agg_dfs) > 1:
        agg_bydt_df = pd.concat(agg_dfs)
        res_bydt_df = pd.concat(res_dfs)
    else:
        agg_bydt_df = agg_dfs[0]
        res_bydt_df = res_dfs[0]

    # Create multi-index based on datetime and catfield
    if catfield is not None:
        midx_fields = catfield.copy()
    else:
        midx_fields = []

    midx_fields.append('datetime')
    agg_bydt_df.set_index(midx_fields, inplace=True, drop=True)
    agg_bydt_df.sort_index(inplace=True)

    # Reorder the columns
    col_order = ['arrivals', 'departures', 'occupancy', 'day_of_week', 'dow_name',
                 'bin_of_day_str', 'bin_of_day', 'bin_of_week']

    agg_bydt_df = agg_bydt_df[col_order]

    bydt_dfs = {'agg': agg_bydt_df, 'highres': res_bydt_df}

    return bydt_dfs


def update_occ(occ, entry_bin, rec_type, list_of_inc_arrays):
    """
    Increment occupancy array

    Parameters
    ----------
    occ
    entry_bin
    rec_type
    list_of_inc_arrays

    Returns
    -------

    """
    num_stop_recs = len(entry_bin)
    for i in range(num_stop_recs):
        if rec_type[i] in ['inner', 'left', 'right', 'outer']:
            pos = entry_bin[i]
            occ_inc = list_of_inc_arrays[i]
            try:
                occ[pos:pos + len(occ_inc)] += occ_inc
            except (IndexError, TypeError) as error:
                raise LookupError(f'pos {pos} occ_inc {occ_inc}\n{error}')


def in_bin_occ_frac(entry_bin: int,
                    in_dt_np: np.datetime64,
                    out_dt_np: np.datetime64,
                    start_analysis_dt_np: np.datetime64,
                    bin_size_minutes: int,
                    edge_bins: int = 1):
    """
    Computes fractional occupancy in arrival (entry) bin.

    Parameters
    ----------
    entry_bin : int
        bin in which entity arrives
    in_dt_np : numpy datetime64[s]
        entry time
    out_dt_np : numpy datetime64[s]
        exit time
    start_analysis_dt_np : numpy datetime64[s]
        datetime to start computing metrics
    bin_size_minutes : int
        bin size in minutes
    edge_bins : int
        1=fractional, 2=whole bin

    Returns
    -------
    Entry bin fraction in [0.0,1.0]

    """

    if edge_bins == 1:
        rel_in_time_secs = (in_dt_np - start_analysis_dt_np).astype('timedelta64[s]').astype(np.float64)
        rel_out_time_secs = (out_dt_np - start_analysis_dt_np).astype('timedelta64[s]').astype(np.float64)
        rel_right_bin_edge_secs = (entry_bin + 1) * bin_size_minutes * 60
        rel_right_edge_secs = np.minimum(rel_out_time_secs, rel_right_bin_edge_secs)
        in_bin_seconds = (rel_right_edge_secs - rel_in_time_secs)
        inbin_occ_frac = in_bin_seconds / (bin_size_minutes * 60.0)
    else:
        # inbin_occ_frac = 1.0
        inbin_occ_frac = np.ones(in_dt_np.size)

    return inbin_occ_frac


# This is new and untested.
def out_bin_occ_frac(exit_bin: int, in_dt_np, out_dt_np, start_analysis_dt_np,
                     bin_size_minutes: int, edge_bins: int = 1):
    """
    Computes fractional occupancy in departure (exit) bin.

    Parameters
    ----------
    exit_bin : int
        bin in which entity arrives
    in_dt_np : numpy datetime64[s]
        entry time
    out_dt_np : numpy datetime64[s]
        exit time
    start_analysis_dt_np : numpy datetime64[s]
        datetime to start computing metrics
    bin_size_minutes : int
        bin size in minutes
    edge_bins : int
        1=fractional, 2=whole bin

    Returns
    -------
    Exit bin fraction in [0.0,1.0]

    """

    if edge_bins == 1:
        rel_in_time_secs = (in_dt_np - start_analysis_dt_np).astype('timedelta64[s]').astype(np.float64)
        rel_out_time_secs = (out_dt_np - start_analysis_dt_np).astype('timedelta64[s]').astype(np.float64)
        rel_left_bin_edge_secs = exit_bin * bin_size_minutes * 60
        rel_left_edge_secs = np.maximum(rel_in_time_secs, rel_left_bin_edge_secs)
        out_bin_seconds = (rel_out_time_secs - rel_left_edge_secs)
        outbin_occ_frac = out_bin_seconds / (bin_size_minutes * 60.0)
    else:
        # outbin_occ_frac = 1.0
        outbin_occ_frac = np.ones(in_dt_np.size)

    return outbin_occ_frac


def make_occ_inc(in_bin: int, out_bin: int,
                 in_frac: float, out_frac: float, occ_weight: float):
    """Create array of occupancy increments for a single stop

    Parameters
    ----------
    in_bin: int
    out_bin: int
    in_frac: float
    out_frac: float
    occ_weight: float

    """
    n_bins = out_bin - in_bin + 1
    if n_bins > 2:
        # [in_frac, occ_weight, occ_weight, ..., out_frac]
        ones = np.ones(n_bins - 2, dtype=np.float64) * occ_weight
        occ_inc = np.concatenate((np.array([in_frac]) * occ_weight, ones, np.array([out_frac]) * occ_weight))
    elif n_bins == 2:
        # [in_frac, out_frac]
        occ_inc = np.concatenate((np.array([in_frac]) * occ_weight, np.array([out_frac]) * occ_weight))
    else:
        # [in_frac]
        occ_inc = np.array([in_frac]) * occ_weight

    return occ_inc


def update_occ_incs(in_bins, out_bins, list_of_inc_arrays, rec_types, num_bins):
    """
    Update the in_bin, out_bin, and occupancy incrementer array for each
    stop record based on the record type.

    Stops that fall entirely within the analysis range (type='inner') are unchanged.
    Stops that arrive (depart) before (after) the start (end) of the analysis range
    are updated to reflect this.

    Parameters
    ----------
    in_bins: List[int]
        Entry bin for each stop
    out_bins: List[int]
        Exit bin for each stop
    list_of_inc_arrays: List[ndarray]
        Occupancy incrementer array for each stop
    rec_types: List[str]
        Record type for each stop
    num_bins: int
        Total number of time bins in analysis range

    """
    num_stop_recs = len(in_bins)
    rectype_counts = {}

    for i in range(num_stop_recs):
        if rec_types[i] == 'inner':
            rectype_counts['inner'] = rectype_counts.get('inner', 0) + 1
        elif rec_types[i] == 'left':
            # arrival is outside analysis window (in_bin < 0)
            rectype_counts['left'] = rectype_counts.get('left', 0) + 1
            new_in_bin = 0
            bin_shift = -1 * in_bins[i]
            new_inc_array = list_of_inc_arrays[i][bin_shift:]
            # Update main arrays
            in_bins[i] = new_in_bin
            list_of_inc_arrays[i] = new_inc_array
        elif rec_types[i] == 'right':
            # departure is outside analysis window (out_bin >= num_bins)
            rectype_counts['right'] = rectype_counts.get('right', 0) + 1
            new_out_bin = num_bins - 1
            bin_shift = out_bins[i] - (num_bins - 1)
            # Keep all but the last bin_shift elements
            new_inc_array = list_of_inc_arrays[i][:-bin_shift]
            # Update main arrays
            out_bins[i] = new_out_bin
            list_of_inc_arrays[i] = new_inc_array
        elif rec_types[i] == 'outer':
            # This is combo of left and right
            rectype_counts['outer'] = rectype_counts.get('outer', 0) + 1
            new_in_bin = 0
            new_out_bin = num_bins - 1
            entry_bin_shift = -1 * in_bins[i]
            exit_bin_shift = out_bins[i] - (num_bins - 1)
            new_inc_array = list_of_inc_arrays[i][entry_bin_shift:-exit_bin_shift]
            # Update main arrays
            in_bins[i] = new_in_bin
            out_bins[i] = new_out_bin
            list_of_inc_arrays[i] = new_inc_array
        elif rec_types[i] == 'backwards':
            rectype_counts['backwards'] = rectype_counts.get('backwards', 0) + 1
        elif rec_types[i] == 'none':
            rectype_counts['none'] = rectype_counts.get('none', 0) + 1
        else:
            rectype_counts['unknown'] = rectype_counts.get('unknown', 0) + 1

    return rectype_counts
