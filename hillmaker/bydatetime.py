"""
The :mod:`hillmaker.bydatetime` module includes functions for computing occupancy,
arrival, and departure statistics by time bin of day and date.
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
from pandas import DataFrame
from pandas import Series
from pandas import Timestamp
from datetime import datetime
from datetime import timedelta
from pandas.tseries.offsets import Minute
import itertools
from timeit import default_timer as timer


from hillmaker.hmlib import *


def make_bydatetime(stops_df, infield, outfield,
                    start_analysis, end_analysis, catfield=None,
                    bin_size_minutes=60,
                    cat_to_exclude=None,
                    totals=1,
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

    start_analysis: datetime
        Start date for the analysis

    end_analysis: datetime
        End date for the analysis

    catfield : string or List of strings, optional
        Column name(s) corresponding to the categories. If none is specified, then only overall occupancy is analyzed.

    bin_size_minutes: int, default 60
        Bin size in minutes. Should divide evenly into 1440.

    cat_to_exclude: list of strings, default None
        Categories to ignore

    edge_bins: int, default 1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=whole bin

    totals: int, default 1
        0=no totals, 1=totals by datetime, 2=totals bydatetime as well as totals for each field in the
        catfields (only relevant for > 1 category field)

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

    bydt_dfs = make_bydatetime(stops_df, 'InTime', 'OutTime',
    ...           datetime(2014, 3, 1), datetime(2014, 6, 30), ['PatientType','Severity'], 60, totals=2)


    TODO
    ----


     Notes
    -----


    References
    ----------


    See Also
    --------
    """

    start_analysis_dt = pd.Timestamp(start_analysis)
    end_analysis_dt = pd.Timestamp(end_analysis)

    # Compute min and max of in and out times
    min_intime = stops_df[infield].min()
    max_intime = stops_df[infield].max()
    min_outtime = stops_df[outfield].min()
    max_outtime = stops_df[outfield].max()

    if verbose:
        print("min of intime: {}".format(min_intime))
        print("max of outtime: {}".format(max_outtime))
        print("max of intime: {}".format(max_intime))
        print("min of outtime: {}".format(min_outtime))

    # TODO - Add warnings here related to min and maxes out of whack with analysis range

    analysis_range = [start_analysis_dt, end_analysis_dt]

    rng_bydt = Series(pd.date_range(start_analysis_dt, end_analysis_dt, freq=Minute(bin_size_minutes)))

    # Handle cases of no catfield, a single fieldname, or a list of fields
    # If no category, add a temporary dummy column populated with a totals str

    CONST_FAKE_CATFIELDNAME = '__FakeCatForTotals__'
    total_str = 'total'

    bTotalsDone = False
    if catfield is not None:
        if isinstance(catfield, str):
            catfield = [catfield]
    else:
        totlist = [total_str]*len(stops_df)
        totseries = Series(totlist,dtype=str,name=[CONST_FAKE_CATFIELDNAME])
        totfield_df = DataFrame({CONST_FAKE_CATFIELDNAME: totseries})
        stops_df = pd.concat([stops_df, totfield_df],axis=1)
        catfield = [CONST_FAKE_CATFIELDNAME]
        bTotalsDone = True

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

    # Now we'll build up the seeded by date table a category at a time.
    # Along the way we'll initialize all the measures to 0.

    # The following doesn't feel very Pythonic, but just trying to get it working for now
    len_bydt = len(rng_bydt)
    all_cat_df = []

    # After the following loops, all_cat_df will be a list of dataframes of just the category
    # field columns
    for p in itertools.product(*categories):
            i=0
            cat_df = DataFrame()
            j=0
            for c in [*p]:
                bydt_catdata = {catfield[j]: [c] * len_bydt}
                cat_df_cat = DataFrame(bydt_catdata, columns=[catfield[j]])
                j+=1
                cat_df = pd.concat([cat_df, cat_df_cat],axis=1)
            all_cat_df.append(cat_df)
            i+=1

    bydt_df = DataFrame()
    bydt_data = {'datetime': rng_bydt, 'arrivals': [0.0] * len_bydt,
                             'departures': [0.0] * len_bydt, 'occupancy': [0.0] * len_bydt}

    bydt_data_df = DataFrame(bydt_data, columns=['datetime', 'arrivals', 'departures', 'occupancy'])

    for cat_df in all_cat_df:
        bydt_df_cat = pd.concat([cat_df, bydt_data_df],axis=1)
        bydt_df = pd.concat([bydt_df, bydt_df_cat])

    # Compute various day and time bin related fields
    bydt_df['day_of_week'] = bydt_df['datetime'].map(lambda x: x.weekday())
    bydt_df['bin_of_day'] = bydt_df['datetime'].map(lambda x: bin_of_day(x, bin_size_minutes))
    bydt_df['bin_of_week'] = bydt_df['datetime'].map(lambda x: bin_of_week(x, bin_size_minutes))

    # Now create a hierarchical multiindex to replace the default index (since it
    # has dups from the concatenation). We keep the columns used in the index as
    # regular columns as well since it's hard
    # to do a column transformation using a specific level of a multiindex.
    # http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64?rq=1

    midx_fields = catfield.copy()
    midx_fields.append('datetime')
    bydt_df.set_index(midx_fields, inplace=True, drop=False)

    bydt_df.sortlevel(inplace=True)

    # Main occupancy, arrivals, departures loop. Process each record in `stops_df`.

    num_processed = 0
    num_inner = 0
    rectype_counts = {}

    for row in stops_df.iterrows():

        intime_raw = row[1][infield]
        outtime_raw = row[1][outfield]

        catseries = row[1][catfield]
        cat = tuple(catseries)

        intime = to_the_second(intime_raw)
        outtime = to_the_second(outtime_raw)
        good_rec = True
        rectype = stoprec_analysis_rltnshp([intime, outtime], analysis_range)
    
        if rectype in ['backwards']:
            good_rec = False
            rectype_counts['backwards'] = rectype_counts.get('backwards', 0) + 1
    
        if good_rec and rectype != 'none':
            indtbin = dt_floor(intime, bin_size_minutes)
            outdtbin = dt_floor(outtime, bin_size_minutes)

            inout_occ_frac = occ_frac([intime, outtime], bin_size_minutes, edge_bins)

            nbins = numbins(indtbin, outdtbin, bin_size_minutes)
            dtbin = indtbin

            if verbose == 2:
                print("{} {} {} {} {:.3f} {:.3f} {:.3f}".format(intime, outtime, str(cat),
                      rectype, timer(), inout_occ_frac[0], inout_occ_frac[1]))

            if rectype == 'inner':
                num_inner += 1
                rectype_counts['inner'] = rectype_counts.get('inner', 0) + 1

                bydt_df.at[(*cat, indtbin), 'occupancy'] += inout_occ_frac[0]
                bydt_df.at[(*cat, indtbin), 'arrivals'] += 1.0
                bydt_df.at[(*cat, outdtbin), 'departures'] += 1.0

                current_bin = 2
                while current_bin < nbins:
                    dtbin += timedelta(minutes=bin_size_minutes)
                    bydt_df.at[(*cat, dtbin), 'occupancy'] += 1.0
                    current_bin += 1

                if nbins > 1:
                    bydt_df.at[(*cat, outdtbin), 'occupancy'] += inout_occ_frac[1]
    
            elif rectype == 'right':
                rectype_counts['right'] = rectype_counts.get('right', 0) + 1
                # departure is outside analysis window
                bydt_df.at[(*cat, indtbin), 'occupancy'] += inout_occ_frac[0]
                bydt_df.at[(*cat, indtbin), 'arrivals'] += 1.0
    
                if isgt2bins(indtbin, outdtbin, bin_size_minutes):
                    current_bin = indtbin + timedelta(minutes=bin_size_minutes)
                    while current_bin <= end_analysis_dt:
                        bydt_df.at[(*cat, current_bin), 'occupancy'] += 1.0
                        current_bin += timedelta(minutes=bin_size_minutes)
    
            elif rectype == 'left':
                rectype_counts['left'] = rectype_counts.get('left', 0) + 1
                # arrival is outside analysis window
                bydt_df.at[(*cat, outdtbin), 'occupancy'] += inout_occ_frac[1]
                bydt_df.at[(*cat, outdtbin), 'departures'] += 1.0
    
                if isgt2bins(indtbin, outdtbin, bin_size_minutes):
                    current_bin = start_analysis_dt
                    while current_bin < outdtbin:
                        bydt_df.at[(*cat, current_bin), 'occupancy'] += 1.0
                        current_bin += timedelta(minutes=bin_size_minutes)
    
            elif rectype == 'outer':
                rectype_counts['outer'] = rectype_counts.get('outer', 0) + 1
                # arrival and departure sandwich analysis window
    
                if isgt2bins(indtbin, outdtbin, bin_size_minutes):
                    current_bin = start_analysis_dt
                    while current_bin <= end_analysis_dt:
                        bydt_df.at[(*cat, current_bin), 'occupancy'] += 1.0
                        current_bin += timedelta(minutes=bin_size_minutes)
    
            else:
                pass
    
            num_processed += 1
            if verbose == 2:
                print(num_processed)

    # If there was no category field, drop the fake field from the index and dataframe
    if catfield[0] == CONST_FAKE_CATFIELDNAME:
        bydt_df.set_index('datetime', inplace=True, drop=False)
        bydt_df = bydt_df[['datetime', 'arrivals', 'departures', 'occupancy',
                           'day_of_week', 'bin_of_day', 'bin_of_week' ]]

    # Store main results bydatetime DataFrame

    bydt_dfs = {}
    totals_key = '_'.join(bydt_df.index.names)
    bydt_dfs[totals_key] = bydt_df

    # Compute totals

    if totals >= 1 and not bTotalsDone:

        bydt_group = bydt_df.groupby(['datetime'])
        totals_key = 'datetime'

        tot_arrivals = bydt_group.arrivals.sum()
        tot_departures = bydt_group.departures.sum()
        tot_occ = bydt_group.occupancy.sum()

        tot_data = [tot_arrivals, tot_departures, tot_occ]

        tot_df = pd.concat(tot_data, axis=1)
        tot_df['day_of_week'] = tot_df.index.map(lambda x: x.weekday())
        tot_df['bin_of_day'] = tot_df.index.map(lambda x: bin_of_day(x, bin_size_minutes))
        tot_df['bin_of_week'] = tot_df.index.map(lambda x: bin_of_week(x, bin_size_minutes))

        tot_df['datetime'] = tot_df.index

        col_order = ['datetime', 'arrivals', 'departures', 'occupancy', 'day_of_week',
                     'bin_of_day', 'bin_of_week']
        tot_df = tot_df[col_order]

        bydt_dfs[totals_key] = tot_df

    # If desired, compute totals over each category field. Only relevant for > 1 category field.
    if totals == 2 and len(catfield) > 1:

        for cat in catfield:
            midx_fields = [cat]
            midx_fields.append('datetime')
            bydt_df.set_index(midx_fields, inplace=True, drop=False)

            totals_key = '_'.join(bydt_df.index.names)

            bydt_group = bydt_df.groupby([cat, 'datetime'])

            tot_arrivals = bydt_group.arrivals.sum()
            tot_departures = bydt_group.departures.sum()
            tot_occ = bydt_group.occupancy.sum()
            tot_data = [tot_arrivals, tot_departures, tot_occ]

            tot_df = pd.concat(tot_data, axis=1)
            tot_df['datetime'] = tot_df.index.get_level_values('datetime')
            tot_df[cat] = tot_df.index.get_level_values(cat)
            tot_df['day_of_week'] = tot_df['datetime'].map(lambda x: x.weekday())
            tot_df['bin_of_day'] = tot_df['datetime'].map(lambda x: bin_of_day(x, bin_size_minutes))
            tot_df['bin_of_week'] = tot_df['datetime'].map(lambda x: bin_of_week(x, bin_size_minutes))

            col_order = [cat, 'datetime', 'arrivals', 'departures', 'occupancy', 'day_of_week',
                         'bin_of_day', 'bin_of_week']

            tot_df = tot_df[col_order]

            bydt_dfs[totals_key] = tot_df

    return bydt_dfs

if __name__ == '__main__':

    pass