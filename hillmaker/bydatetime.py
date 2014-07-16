# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 23:50:39 2013

@author: mark
"""

__author__ = 'isken'

import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from datetime import timedelta
from itertools import zip_longest
import time


def make_bydatetime(stops_df,infield,outfield,catfield,start_date,end_date,total_str='Total',bin_size_mins=60):
    """
    Create bydatetime table based on user inputs.

    This is the table from which summary statistics can be computed.

    Parameters
    ----------
    D : pandas DataFrame
       Stop data

    infield : string
       Name of column in D to use as arrival datetime

    outfield : string
       Name of column in D to use as departure datetime

    catfield : string
       Name of column in D to use as category field

    total_str : string
       Value to use for the totals

    bin_size_mins : int
       Bin size in minutes. Should divide evenly into 1440.

    Returns
    -------
    bydatetime: pandas DataFrame
       The computed bydatetime table as a DataFrame

    Examples
    --------
    >>> bydt_df = make_bydatetime(stops_df,'InTime','OutTime','PatientType',
    ...                        datetime(2014, 3, 1),datetime(2014, 6, 30),'Total',60)


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


    import hillpylib as hlib

    from pandas.tseries.offsets import Minute

    analysis_range = [start_date, end_date]

    # Create date and range and convert it from a pandas DateTimeIndex to a
    # reqular old array of datetimes to try to get around the weird problems
    # in computing day of week on datetime64 values.
    # bin_freq = str(bin_size_mins) + 'min'
    #rng_bydt = pd.date_range(start_date, end_date, freq=bin_freq).to_pydatetime()
    #rng_bydt = pd.date_range(start_date, end_date, freq=bin_freq)

    rng_bydt = pd.date_range(start_date, end_date, freq=Minute(bin_size_mins))

    print ("rng_bydt created: {}".format(time.clock()))

    # import sys
    # sys.exit("Stopping after rng_bydt_list creation")
    #
    # num_days = (end_date-start_date).days + 1
    # num_periods = num_days * (1440//bin_size_mins)
    # print(num_periods)
    #
    # # The following is no faster than the pandas date_range() method.
    # #rng_bydt = [start_date + timedelta(minutes=i*60) for i in range(num_periods)]
    # rng_int = [100 + i*60 for i in range(num_periods)]
    #
    # print ("rng_bydt list created: {}".format(time.clock()))




    # Get the unique category values
    categories = [c for c in stops_df[catfield].unique()]

    print ("found unique categories: {}".format(time.clock()))


    # Create a list of column names for the by date table and then an empty data frame based on these columns.
    columns=['category','datetime','arrivals','departures','occupancy']
    bydt_df = DataFrame(columns=columns)

    # Now we'll build up the seeded by date table a category at a time.
    # Along the way we'll initialize all the measures to 0.

    len_bydt = len(rng_bydt)
    for cat in categories:
        bydt_data = {'category': [cat] * len_bydt, 'datetime': rng_bydt, 'arrivals': [0.0] * len_bydt,
                     'departures': [0.0] * len_bydt, 'occupancy': [0.0] * len_bydt}

        bydt_df_cat = DataFrame(bydt_data,columns=['category',
                       'datetime',
                       'arrivals',
                       'departures',
                       'occupancy'])

        bydt_df = pd.concat([bydt_df,bydt_df_cat])


    print ("Seeded bydatetime DataFrame created: {}".format(time.clock()))

    # Now create a hierarchical multiindex to replace the default index (since it
    # has dups from the concatenation). We keep the columns used in the index as
    # regular columns as well since it's hard
    # to do a column transformation using a specific level of a multiindex.
    # http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64?rq=1

    bydt_df = bydt_df.set_index(['category', 'datetime'], drop=False)

    print ("Multi-index on bydatetime DataFrame created: {}".format(time.clock()))

    bydt_df['dayofweek'] = bydt_df['datetime'].map(lambda x: x.weekday())
    bydt_df['bin_of_day'] =  bydt_df['datetime'].map(lambda x: hlib.bin_of_day(x,bin_size_mins))
    bydt_df['bin_of_week'] = bydt_df['datetime'].map(lambda x: hlib.bin_of_week(x,bin_size_mins))

    print ("dayofweek, bin_of_day, bin_of_week computed: {}".format(time.clock()))
    # Main occupancy, arrivals, departures loop. Process each record in the
# stop data file.

    # The following "standard approach" is slow and very non-Pythonic
    # This

    num_processed = 0
    for intime, outtime, cat in zip_longest(stops_df[infield], stops_df[outfield], stops_df[catfield]):
        good_rec = True
        rectype = hlib.stoprec_analysis_rltnshp([intime,outtime],analysis_range)
    
        if rectype in ['backwards']:
            # print "ERROR_{}: {} {} {}".format(rectype,intime,outtime,cat)
            good_rec = False
    
        if good_rec and rectype != 'none':
            indtbin = hlib.dt_floor(intime,bin_size_mins)
            #print indtbin
            outdtbin = hlib.dt_floor(outtime,bin_size_mins)
            inout_occ_frac = hlib.occ_frac([intime, outtime], bin_size_mins)
            
            # print "{} {} {} {} {:.3f} {:.3f} {:.3f}".format(intime, outtime, cat,
            #    rectype, time.clock(), inout_occ_frac[0], inout_occ_frac[1])
    
            if rectype == 'inner':
                bydt_df.ix[(cat,indtbin), 'occupancy'] += inout_occ_frac[0]
                bydt_df.ix[(cat,outdtbin), 'occupancy'] += inout_occ_frac[1]
                bydt_df.ix[(cat,indtbin), 'arrivals'] += 1.0
                bydt_df.ix[(cat,outdtbin), 'departures'] += 1.0
    
                if hlib.isgt2bins(indtbin, outdtbin, bin_size_mins):
                    bin = indtbin + timedelta(minutes=bin_size_mins)
                    while bin < outdtbin:
                        bydt_df.ix[(cat,bin), 'occupancy'] += 1.0
                        bin += timedelta(minutes=bin_size_mins)
    
    
            elif rectype == 'right':
                # departure is outside analysis window
                bydt_df.ix[(cat,indtbin), 'occupancy'] += inout_occ_frac[0]
                bydt_df.ix[(cat,indtbin), 'arrivals'] += 1.0
    
                if hlib.isgt2bins(indtbin, outdtbin, bin_size_mins):
                    bin = indtbin + timedelta(minutes=bin_size_mins)
                    while bin <= end_analysis_dt:
                        bydt_df.ix[(cat,bin), 'occupancy'] += 1.0
                        bin += timedelta(minutes=bin_size_mins)
    
            elif rectype == 'left':
                # arrival is outside analysis window
                bydt_df.ix[(cat,outdtbin), 'occupancy'] += inout_occ_frac[1]
                bydt_df.ix[(cat,outdtbin), 'departures'] += 1.0
    
                if hlib.isgt2bins(indtbin, outdtbin, bin_size_mins):
                    bin = start_analysis_dt + timedelta(minutes=bin_size_mins)
                    while bin < outdtbin:
                        bydt_df.ix[(cat,bin), 'occupancy'] += 1.0
                        bin += timedelta(minutes=bin_size_mins)
    
            elif rectype == 'outer':
                # arrival and departure sandwich analysis window
    
                if hlib.isgt2bins(indtbin, outdtbin, bin_size_mins):
                    bin = start_analysis_dt
                    while bin <= end_analysis_dt:
                        bydt_df.ix[(cat,bin), 'occupancy'] += 1.0
                        bin += timedelta(minutes=bin_size_mins)
    
            else:
                pass
    
            num_processed += 1
            #print numprocessed

    print ("Done processing {} stop recs: {}".format(num_processed, time.clock()))


    return bydt_df



if __name__ == '__main__':

    scenario_name = 'sstest'
    in_fld_name = 'InRoomTS'
    out_fld_name = 'OutRoomTS'
    cat_fld_name = 'PatType'
    file_stopdata = 'data/ShortStay.csv'
    file_stopdata_pkl = 'data/ShortStay.pkl'
    start_analysis = '1/2/1996'
    end_analysis = '3/31/1996 23:45'
    ## Convert string dates to actual datetimes
    start_analysis_dt = pd.Timestamp(start_analysis)
    end_analysis_dt = pd.Timestamp(end_analysis)

    df = pd.read_pickle(file_stopdata_pkl)
    print ("Pickled stop data file read: {}".format(time.clock()))
    bydt_df = make_bydatetime(df,in_fld_name,out_fld_name,cat_fld_name,start_analysis_dt,end_analysis_dt,'Total',60)

    file_bydt_csv = 'bydatetime_' + scenario_name + '.csv'
    bydt_df.to_csv(file_bydt_csv)