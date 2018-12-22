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

import numpy as np
import pandas as pd
from pandas import DataFrame
from pandas import Timestamp
from datetime import datetime
from datetime import timedelta
from timeit import default_timer as timer

from . import hmlib

from pandas.tseries.offsets import Minute


def make_bydatetime(stops_df, infield, outfield,
                    start_analysis, end_analysis, catfield,
                    total_str='Total',
                    bin_size_minutes=60,
                    cat_to_exclude=None,
                    totals=True,
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

    catfield: string, default=''
        Name of column in stops_df to use as category field

    total_str: string, default 'Total'
        Value to use for the totals

    bin_size_minutes: int, default 60
        Bin size in minutes. Should divide evenly into 1440.

    cat_to_exclude: list of str, default None
        Categories to ignore

    totals: bool, default True
        If true, overall totals are computed. Else, just category specific values computed.

    edge_bins: int, default 1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=whole bin


    verbose : int, default 0
        The verbosity level. The default, zero, means silent mode.

    Returns
    -------
    DataFrame
       Occupancy, arrivals, departures by category by datetime bin

    Examples
    --------
    bydt_df = make_bydatetime(stops_df,'InTime','OutTime',
    ...                        datetime(2014, 3, 1),datetime(2014, 6, 30),'PatientType','Total',60)


    TODO
    ----

    - add parameter and code to handle occ frac choice
    - generalize to handle choice of arr, dep, occ or some combo of

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
    max_outtime = stops_df[outfield].max()

    if verbose:
        print("min of intime: {}".format(min_intime))
        print("max of outtime: {}".format(max_outtime))


    # TODO - Add warnings here related to min and maxes out of whack with analysis range

    analysis_range = [start_analysis_dt, end_analysis_dt]

    # Create date and range and convert it from a pandas DateTimeIndex to a
    # reqular old array of datetimes to try to get around the weird problems
    # in computing day of week on datetime64 values.
    # bin_freq = str(bin_size_minutes) + 'min'
    # rng_bydt = pd.date_range(start_date, end_date, freq=bin_freq).to_pydatetime()
    # rng_bydt = pd.date_range(start_date, end_date, freq=bin_freq)

    rng_bydt = pd.date_range(start_analysis_dt, end_analysis_dt, freq=Minute(bin_size_minutes))
    # datebins = pd.DataFrame(index=rng_bydt)

    # Get the unique category values and exclude any specified to exclude
    categories_all = [c for c in stops_df[catfield].unique()]
    if cat_to_exclude is not None:
        categories = [c for c in categories_all if c not in cat_to_exclude]
    else:
        categories = [c for c in categories_all]

    stops_df = stops_df[stops_df[catfield].isin(categories)]

    # Create a list of column names for the by datetime table and then an empty data frame based on these columns.
    columns = ['category', 'datetime', 'arrivals', 'departures', 'occupancy']
    bydt_df = DataFrame(columns=columns)

    # Now we'll build up the seeded by date table a category at a time.
    # Along the way we'll initialize all the measures to 0.

    len_bydt = len(rng_bydt)
    for cat in categories:
        bydt_data = {'category': [cat] * len_bydt, 'datetime': rng_bydt, 'arrivals': np.zeros(len_bydt),
                     'departures': np.zeros(len_bydt), 'occupancy': np.zeros(len_bydt)}

        bydt_df_cat = DataFrame(bydt_data, columns=['category', 'datetime', 'arrivals', 'departures', 'occupancy'])

        bydt_df = pd.concat([bydt_df, bydt_df_cat])

    # Now create a hierarchical multiindex to replace the default index (since it
    # has dups from the concatenation). We keep the columns used in the index as
    # regular columns as well since it's hard
    # to do a column transformation using a specific level of a multiindex.
    # http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64?rq=1

    bydt_df['day_of_week'] = bydt_df['datetime'].map(lambda x: x.weekday())
    bydt_df['bin_of_day'] = bydt_df['datetime'].map(lambda x: hmlib.bin_of_day(x, bin_size_minutes))
    bydt_df['bin_of_week'] = bydt_df['datetime'].map(lambda x: hmlib.bin_of_week(x, bin_size_minutes))

    # Let's try getting rid of column version since it's causing problems in new pandas versions
    bydt_df.set_index(['category', 'datetime'], inplace=True, drop=True)

    bydt_df.sort_index(inplace=True)

    # Main occupancy, arrivals, departures loop. Process each record in `stops_df`.

    num_processed = 0
    num_inner = 0
    rectype_counts = {}

    for intime_raw, outtime_raw, cat in zip(stops_df[infield], stops_df[outfield], stops_df[catfield]):
        intime = hmlib.to_the_second(intime_raw)
        outtime = hmlib.to_the_second(outtime_raw)
        good_rec = True
        rectype = hmlib.stoprec_analysis_rltnshp([intime, outtime], analysis_range)
    
        if rectype in ['backwards']:
            good_rec = False
            rectype_counts['backwards'] = rectype_counts.get('backwards', 0) + 1
    
        if good_rec and rectype != 'none':
            indtbin = hmlib.dt_floor(intime, bin_size_minutes)
            outdtbin = hmlib.dt_floor(outtime, bin_size_minutes)

            inout_occ_frac = hmlib.occ_frac([intime, outtime], bin_size_minutes, edge_bins)

            numbins = hmlib.numbins(indtbin, outdtbin, bin_size_minutes)
            dtbin = indtbin

            if verbose == 2:
                print("{} {} {} {} {:.3f} {:.3f} {:.3f}".format(intime, outtime, cat,
                      rectype, timer(), inout_occ_frac[0], inout_occ_frac[1]))

            if rectype == 'inner':
                num_inner += 1
                rectype_counts['inner'] = rectype_counts.get('inner', 0) + 1

                # Increment arrivals and departures
                bydt_df.loc[(cat, indtbin), 'arrivals'] += 1.0
                bydt_df.at[(cat, outdtbin), 'departures'] += 1.0

                # Increment occupancy - I've tried to find a faster approach but
                # use of at appears to be fastest.

                # bydt_df.at[(cat, indtbin), 'occupancy'] += inout_occ_frac[0]
                # if numbins > 1:
                #     bydt_df.at[(cat, outdtbin), 'occupancy'] += inout_occ_frac[1]

                current_bin = 2
                while current_bin < numbins:
                    dtbin += timedelta(minutes=bin_size_minutes)
                    bydt_df.at[(cat, dtbin), 'occupancy'] += 1.0
                    current_bin += 1

                # The following is much slower. Slicing is expensive.
                # Create array of ones as initial occupancy increment
                # occinc = np.ones(int(numbins))

                # Update array for inbin fraction
                #occinc[0] = inout_occ_frac[0]

                # Update array for outbin fraction
                #if numbins > 1:
                #    occinc[-1] += inout_occ_frac[1]

                # Add the occ increment array to appropriate slice in dataframe
                #bydt_df.loc[(cat, slice(indtbin, outdtbin)), 'occupancy'] += occinc
    
            elif rectype == 'right':
                rectype_counts['right'] = rectype_counts.get('right', 0) + 1
                # departure is outside analysis window
                bydt_df.at[(cat, indtbin), 'occupancy'] += inout_occ_frac[0]
                bydt_df.at[(cat, indtbin), 'arrivals'] += 1.0
    
                if hmlib.isgt2bins(indtbin, outdtbin, bin_size_minutes):
                    current_bin = indtbin + timedelta(minutes=bin_size_minutes)
                    while current_bin <= end_analysis_dt:
                        bydt_df.at[(cat, current_bin), 'occupancy'] += 1.0
                        current_bin += timedelta(minutes=bin_size_minutes)
    
            elif rectype == 'left':
                rectype_counts['left'] = rectype_counts.get('left', 0) + 1
                # arrival is outside analysis window
                bydt_df.at[(cat, outdtbin), 'occupancy'] += inout_occ_frac[1]
                bydt_df.at[(cat, outdtbin), 'departures'] += 1.0
    
                if hmlib.isgt2bins(indtbin, outdtbin, bin_size_minutes):
                    current_bin = start_analysis_dt
                    while current_bin < outdtbin:
                        bydt_df.at[(cat, current_bin), 'occupancy'] += 1.0
                        current_bin += timedelta(minutes=bin_size_minutes)
    
            elif rectype == 'outer':
                rectype_counts['outer'] = rectype_counts.get('outer', 0) + 1
                # arrival and departure sandwich analysis window
    
                if hmlib.isgt2bins(indtbin, outdtbin, bin_size_minutes):
                    current_bin = start_analysis_dt
                    while current_bin <= end_analysis_dt:
                        bydt_df.at[(cat, current_bin), 'occupancy'] += 1.0
                        current_bin += timedelta(minutes=bin_size_minutes)
    
            else:
                pass
    
            num_processed += 1
            if verbose == 2:
                print(num_processed)

    # Compute totals
    if totals:
        bydt_group = bydt_df.groupby('datetime')

        tot_arrivals = bydt_group.arrivals.sum()
        tot_departures = bydt_group.departures.sum()
        tot_occ = bydt_group.occupancy.sum()

        tot_data = [tot_arrivals, tot_departures, tot_occ]
        tot_df = pd.concat(tot_data, axis=1, keys=[s.name for s in tot_data])
        tot_df['day_of_week'] = tot_df.index.map(lambda x: x.weekday())
        tot_df['bin_of_day'] = tot_df.index.map(lambda x: hmlib.bin_of_day(x, bin_size_minutes))
        tot_df['bin_of_week'] = tot_df.index.map(lambda x: hmlib.bin_of_week(x, bin_size_minutes))

        tot_df['category'] = total_str
        tot_df.set_index('category', append=True, inplace=True, drop=True)
        tot_df = tot_df.reorder_levels(['category', 'datetime'])
        # tot_df['datetime'] = tot_df.index.levels[1]

        col_order = ['arrivals', 'departures', 'occupancy', 'day_of_week',
                     'bin_of_day', 'bin_of_week']
        tot_df = tot_df[col_order]
        bydt_df = bydt_df.append(tot_df)

    return bydt_df

if __name__ == '__main__':

    pass