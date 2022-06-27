"""
The :mod:`hillmaker.bydatetime` module includes functions for computing occupancy,
arrival, and departure statistics by time bin of day and date.
"""

# Copyright 2022 Mark Isken
#
import logging

import numpy as np
import pandas as pd
from pandas import DataFrame
from pandas import Series
from pandas import Timestamp
from datetime import datetime
from pandas.tseries.offsets import Minute

import hillmaker.hmlib as hmlib

CONST_FAKE_OCCWEIGHT_FIELDNAME = 'FakeOccWeightField'
CONST_FAKE_CATFIELD_NAME = 'FakeCatForTotals'
OCC_TOLERANCE = 0.02

# This should inherit level from root logger
logger = logging.getLogger(__name__)


def make_bydatetime(stops_df, infield, outfield,
                    start_analysis_np, end_analysis_np, catfield=None,
                    bin_size_minutes=60,
                    cat_to_exclude=None,
                    totals=1,
                    occ_weight_field=None,
                    edge_bins=1,
                    verbose=0):
    """
    Create bydatetime table based on user inputs.

    This is the table from which summary statistics can be computed.

    Parameters
    ----------
    stops_df: DataFrame
        Stop data

    infield: string
        Name of column in stops_df to use as arrival datetime

    outfield: string
        Name of column in stops_df to use as departure datetime

    start_analysis_np: numpy datetime64[ns]
        Start date for the analysis

    end_analysis_np: numpy datetime64[ns]
        End date for the analysis

    catfield : string, optional
        Column name corresponding to the categories. If none is specified, then only overall occupancy is analyzed.

    bin_size_minutes: int, default 60
        Bin size in minutes. Should divide evenly into 1440.

    cat_to_exclude: list of strings, default None
        Categories to ignore

    edge_bins: int, default 1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=whole bin

    totals: int, default 1
        0=no totals, 1=totals by datetime, 2=totals bydatetime as well as totals for each field in the
        catfields (only relevant for > 1 category field)

    occ_weight_field : string, optional (default=1.0)
        Column name corresponding to the weights to use for occupancy incrementing.

    verbose : int, default 0
        The verbosity level. The default, zero, means silent mode.

    Returns
    -------
    Dict of DataFrames
       Occupancy, arrivals, departures by category by datetime bin

    Examples
    --------
    bydt_dfs = make_bydatetime(stops_df, 'InTime', 'OutTime',
    ...                        datetime(2014, 3, 1), datetime(2014, 6, 30), 'PatientType', 60)




    TODO
    ----
    * Sanity checks on date ranges
    * Formal test using short stay data
    * Flow conservation checks


    Notes
    -----


    References
    ----------


    See Also
    --------
    """
    # Number of bins in analysis span
    num_bins = hmlib.bin_of_span(end_analysis_np, start_analysis_np, bin_size_minutes) + 1

    # Compute min and max of in and out times
    min_intime = stops_df[infield].min()
    max_intime = stops_df[infield].max()
    min_outtime = stops_df[outfield].min()
    max_outtime = stops_df[outfield].max()

    logger.info(f"min of intime: {min_intime}")
    logger.info(f"max of intime: {max_intime}")
    logger.info(f"min of outtime: {min_outtime}")
    logger.info(f"max of outtime: {max_outtime}")

    # TODO - Add warnings here related to min and maxes out of whack with analysis range

    # Occupancy weights
    # If no occ weight field specified, create fake one containing 1.0 as values.
    # Avoids having to check during dataframe iteration whether or not to use
    # default occupancy weight.

    if occ_weight_field is None:
        occ_weight_vec = np.ones(len(stops_df.index), dtype=np.float64)
        occ_weight_df = DataFrame({CONST_FAKE_OCCWEIGHT_FIELDNAME: occ_weight_vec})
        stops_df = pd.concat([stops_df, occ_weight_df], axis=1)
        occ_weight_field = CONST_FAKE_OCCWEIGHT_FIELDNAME

    # Handle cases of no catfield, or a single fieldname, (no longer supporting a list of fieldnames)
    # If no category, add a temporary dummy column populated with a totals str

    total_str = 'total'

    do_totals = True
    if catfield is not None:
        # If it's a string, it's a single cat field --> convert to list
        # Keeping catfield as a list in case I change mind about multiple category fields
        if isinstance(catfield, str):
            catfield = [catfield]
    else:
        totlist = [total_str] * len(stops_df)
        totseries = Series(totlist, dtype=str, name=CONST_FAKE_CATFIELD_NAME)
        totfield_df = DataFrame({CONST_FAKE_CATFIELD_NAME: totseries})
        stops_df = pd.concat([stops_df, totfield_df], axis=1)
        catfield = [CONST_FAKE_CATFIELD_NAME]
        do_totals = False

    # Get the unique category values and exclude any specified to exclude
    categories = []
    if cat_to_exclude is not None:
        for i in range(len(catfield)):
            categories.append(tuple([c for c in stops_df[catfield[i]].unique() if c not in cat_to_exclude[i]]))
    else:
        for i in range(len(catfield)):
            categories.append(tuple([c for c in stops_df[catfield[i]].unique()]))

    for i in range(len(catfield)):
        stops_df = stops_df[stops_df[catfield[i]].isin(categories[i])]

    # TEMPORARY ASSUMPTION - only a single category field is allowed
    # Main loop over the categories. Filter stops_df by category and then do
    # numpy based occupancy computations.
    results = {}
    for cat in categories[0]:
        cat_df = stops_df[stops_df[catfield[0]] == cat]
        num_stop_recs = len(cat_df)

        # Convert Series to numpy arrays for infield, outfield, occ_weight
        in_ts_np = cat_df[infield].to_numpy()
        out_ts_np = cat_df[outfield].to_numpy()
        occ_weight = cat_df[occ_weight_field].to_numpy()

        # Compute entry and exit bin arrays
        entry_bin = hmlib.bin_of_span(in_ts_np, start_analysis_np, bin_size_minutes)
        exit_bin = hmlib.bin_of_span(out_ts_np, start_analysis_np, bin_size_minutes)

        # Compute inbin and outbin fraction arrays
        entry_bin_frac = in_bin_occ_frac(entry_bin, in_ts_np, out_ts_np,
                                         start_analysis_np, bin_size_minutes, edge_bins=1)
        exit_bin_frac = out_bin_occ_frac(exit_bin, in_ts_np, out_ts_np,
                                         start_analysis_np, bin_size_minutes, edge_bins=1)

        # Create list of occupancy incrementor arrays
        list_of_inc_arrays = [make_occ_incs(entry_bin[i], exit_bin[i],
                                            entry_bin_frac[i], exit_bin_frac[i],
                                            occ_weight[i]) for i in range(num_stop_recs)]
        # if verbose == 2:
        #     with open(f'./output/{cat}_occ_incs.csv', 'w') as fout:
        #
        #         # using csv.writer method from CSV package
        #         write = csv.writer(fout, lineterminator='\n')
        #         write.writerows(list_of_inc_arrays)

        # Create array of stop record types
        rec_type = cat_df.apply(lambda x:
                                hmlib.stoprec_analysis_rltnshp(x[infield], x[outfield],
                                                               start_analysis_np, end_analysis_np), axis=1).to_numpy()

        # Do the occupancy incrementing
        rec_counts = update_occ_incs(entry_bin, exit_bin, list_of_inc_arrays, rec_type, num_bins)
        logger.info(f'cat {cat} {rec_counts}')

        occ = np.zeros(num_bins, dtype=np.float64)
        update_occ(occ, entry_bin, rec_type, list_of_inc_arrays)

        # Count arrivals and departures by bin
        arr = np.bincount(entry_bin, minlength=num_bins).astype(np.float64)
        dep = np.bincount(exit_bin, minlength=num_bins).astype(np.float64)

        # Combine arr, dep, occ (in that order) into matrix
        occ_arr_dep = np.column_stack((arr, dep, occ))

        # Conservation of flow checks for num arrivals and departures
        num_arrivals_hm = arr.sum()
        num_departures_hm = dep.sum()

        num_arrivals_stops = cat_df.loc[(cat_df[infield] >= start_analysis_np) &
                                        (cat_df[infield] <= end_analysis_np)].index.size

        num_departures_stops = cat_df.loc[(cat_df[outfield] >= start_analysis_np) &
                                        (cat_df[outfield] <= end_analysis_np)].index.size

        logger.info(f'cat {cat} num_arrivals_hm {num_arrivals_hm} num_arrivals_stops {num_arrivals_stops}')
        logger.info(
            f'cat {cat} num_departures_hm {num_departures_hm} num_departures_stops {num_departures_stops}')

        if num_arrivals_hm != num_arrivals_stops:
            logger.warning(
                f'num_arrivals_hm ({num_arrivals_hm}) not equal to num_arrivals_stops ({num_arrivals_stops})')

        if num_departures_hm != num_departures_stops:
            logger.warning(
                f'num_departures_hm ({num_departures_hm}) not equal to departures_stops ({num_departures_stops})')

        # Conservation of flow checks for weighted occupancy
        tot_occ_him = occ.sum()

        tot_occ_mins_stops = \
            (cat_df[occ_weight_field] * (cat_df[outfield] - cat_df[infield]).dt.total_seconds()).sum() / 60
        tot_occ_stops = tot_occ_mins_stops / bin_size_minutes

        logger.info(f'cat {cat} tot_occ_hm {tot_occ_him:.2f} tot_occ_stops {tot_occ_stops:.2f}')
        if (tot_occ_him - tot_occ_stops) / tot_occ_stops > OCC_TOLERANCE:
            logger.warning(
                f'cat {cat} Weighted occupancy differs by more than {OCC_TOLERANCE})')

        # Store results
        results[cat] = occ_arr_dep

    # Convert stacked arrays to a Dataframe
    bydt_df_cat = arrays_to_df(results, start_analysis_np, end_analysis_np, bin_size_minutes, catfield)

    # Store main results bydatetime DataFrame
    bydt_dfs = {}
    totals_key = '_'.join(bydt_df_cat.index.names)
    bydt_dfs[totals_key] = bydt_df_cat.copy()

    # Do totals if there was at least one category field
    if do_totals:
        results_totals = {}
        totals_key = 'datetime'
        total_occ_arr_dep = np.zeros((num_bins, 3), dtype=np.float64)
        for cat, oad_array in results.items():
            total_occ_arr_dep += oad_array

        results_totals[totals_key] = total_occ_arr_dep
        bydt_df_total = arrays_to_df(results_totals, start_analysis_np, end_analysis_np, bin_size_minutes)
        bydt_dfs[totals_key] = bydt_df_total

    return bydt_dfs


def arrays_to_df(results_arrays, start_analysis_dt, end_analysis_dt, bin_size_minutes, catfield=None):
    """
    Converts results dict from ndarrays to Dataframes

    results_arrays: dict of ndarrays
    """

    bydt_dfs = {}
    rng_bydt = Series(pd.date_range(start_analysis_dt, end_analysis_dt, freq=Minute(bin_size_minutes)))

    dfs = []
    for cat, oad_array in results_arrays.items():
        # Create Dataframe from ndarray
        df = pd.DataFrame(oad_array, columns=['arrivals', 'departures', 'occupancy'])

        # Add datetime column and category column (still assuming just one category field)
        df['datetime'] = rng_bydt
        if catfield:
            for c in catfield:
                df[c] = cat

        df['day_of_week'] = df['datetime'].map(lambda x: x.weekday())
        df['dow_name'] = df['datetime'].map(lambda x: x.day_name())
        df['bin_of_day'] = df['datetime'].map(lambda x: hmlib.bin_of_day(x, bin_size_minutes))
        df['bin_of_week'] = df['datetime'].map(lambda x: hmlib.bin_of_week(x, bin_size_minutes))

        dfs.append(df)  # Add category specific dataframe to list

    # Concatenate the dfs in cat_dfs
    if len(dfs) > 1:
        bydt_df = pd.concat(dfs)
    else:
        bydt_df = dfs[0]

    # Create multi-index based on datetime and catfield
    if catfield is not None:
        midx_fields = catfield.copy()
    else:
        midx_fields = []

    midx_fields.append('datetime')
    bydt_df.set_index(midx_fields, inplace=True, drop=True)
    bydt_df.sort_index(inplace=True)

    # Reorder the columns
    col_order = ['arrivals', 'departures', 'occupancy', 'day_of_week', 'dow_name',
                 'bin_of_day', 'bin_of_week']

    bydt_df = bydt_df[col_order]

    return bydt_df


def update_occ(occ, entry_bin, rec_type, list_of_inc_arrays):
    num_stop_recs = len(entry_bin)
    for i in range(num_stop_recs):
        if rec_type[i] in ['inner', 'left', 'right', 'outer']:
            pos = entry_bin[i]
            occ_inc = list_of_inc_arrays[i]
            try:
                occ[pos:pos + len(occ_inc)] += occ_inc
            except (IndexError, TypeError) as error:
                raise Exception(f'pos {pos} occ_inc {occ_inc}\n{error}')


def in_bin_occ_frac(entry_bin, in_dt_np, out_dt_np, start_analysis_dt_np, bin_size_minutes, edge_bins=1):
    """
    Computes fractional occupancy in inbin and outbin.

    Parameters
    ----------
    in_dt_np: entry time (numpy datetime74[s])
    bin_size_minutes: bin size in minutes
    edge_bins: 1=fractional, 2=whole bin

    Returns
    -------
    [inbin frac, outbin frac] where each is a real number in [0.0,1.0]

    """

    # inbin occupancy
    if edge_bins == 1:
        rel_in_time_secs = (in_dt_np - start_analysis_dt_np).astype('timedelta64[s]').astype(np.float64)
        rel_out_time_secs = (out_dt_np - start_analysis_dt_np).astype('timedelta64[s]').astype(np.float64)
        rel_right_bin_edge_secs = (entry_bin + 1) * bin_size_minutes * 60
        rel_right_edge_secs = np.minimum(rel_out_time_secs, rel_right_bin_edge_secs)
        in_bin_seconds = (rel_right_edge_secs - rel_in_time_secs)
        inbin_occ_frac = in_bin_seconds / (bin_size_minutes * 60.0)
    else:
        inbin_occ_frac = 1.0

    return inbin_occ_frac

# This is new and untested.
def out_bin_occ_frac(exit_bin, in_ts, out_ts, start_analysis_np, bin_size_minutes, edge_bins=1):
    """
    Computes fractional occupancy in inbin and outbin.

    Parameters
    ----------
    in_ts: entry time (Timestamp)
    bin_size_minutes: bin size in minutes
    edge_bins: 1=fractional, 2=whole bin

    Returns
    -------
    [inbin frac, outbin frac] where each is a real number in [0.0,1.0]

    """

    # inbin occupancy
    if edge_bins == 1:
        rel_in_time_secs = (in_ts - start_analysis_np).astype('timedelta64[s]').astype(np.float64)
        rel_out_time_secs = (out_ts - start_analysis_np).astype('timedelta64[s]').astype(np.float64)
        rel_left_bin_edge_secs = exit_bin * bin_size_minutes * 60
        rel_left_edge_secs = np.maximum(rel_in_time_secs, rel_left_bin_edge_secs)
        out_bin_seconds = (rel_out_time_secs - rel_left_edge_secs)
        outbin_occ_frac = out_bin_seconds / (bin_size_minutes * 60.0)
    else:
        outbin_occ_frac = 1.0

    return outbin_occ_frac


def make_occ_incs(in_bin, out_bin, in_frac, out_frac, occ_weight):
    n_bins = out_bin - in_bin + 1
    if n_bins > 2:
        ones = np.ones(n_bins - 2, dtype=np.float64) * occ_weight
        occ_incs = np.concatenate((np.array([in_frac]) * occ_weight, ones, np.array([out_frac]) * occ_weight))
    elif n_bins == 2:
        occ_incs = np.concatenate((np.array([in_frac]) * occ_weight, np.array([out_frac]) * occ_weight))
    else:
        occ_incs = np.array([in_frac]) * occ_weight

    return occ_incs


def update_occ_incs(in_bins, out_bins, list_of_inc_arrays, rec_types, num_bins):
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


if __name__ == '__main__':
    # Required inputs
    scenario = 'sslittle_ex01'
    in_fld_name = 'InRoomTS'
    out_fld_name = 'OutRoomTS'
    # cat_fld_name = 'PatType'
    start_analysis = '1/1/1996'
    end_analysis = '1/3/1996 23:45'

    # Optional inputs
    verbose = 1
    output_path = './output/'

    # Create dfs
    file_stopdata = './data/ShortStay.csv'
    ss_df = pd.read_csv(file_stopdata, parse_dates=[in_fld_name, out_fld_name])

    dfs = make_bydatetime(ss_df, in_fld_name, out_fld_name, Timestamp(start_analysis), Timestamp(end_analysis))

    print(dfs.keys())
