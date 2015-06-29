# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 23:50:39 2013

@author: mark
"""

__author__ = 'isken'


import pandas as pd
from pandas import DataFrame
from pandas import Timestamp
from datetime import datetime
from datetime import timedelta


from timeit import default_timer as timer

import hillpylib as hm

from pandas.tseries.offsets import Minute


def make_bydatetime(stops_df,infield,outfield,catfield,
                    start_analysis,end_analysis,
                    total_str='Total',
                    bin_size_minutes=60,
                    categories=False,
                    totals=True):
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

    start_date : datetime
       Start date for the analysis

    end_date : datetime
       End date for the analysis

    total_str : string
       Value to use for the totals

    bin_size_minutes : int
       Bin size in minutes. Should divide evenly into 1440.

    Returns
    -------
    bydatetime: pandas DataFrame
       The computed bydatetime table as a DataFrame

    Examples
    --------
    bydt_df = make_bydatetime(stops_df,'InTime','OutTime','PatientType',
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


    start = timer()

    start_analysis_dt = pd.Timestamp(start_analysis)
    end_analysis_dt = pd.Timestamp(end_analysis)

    # Compute min and max of in and out times
    min_intime = stops_df[infield].min()
    max_intime = stops_df[infield].max()
    min_outtime = stops_df[outfield].min()
    max_outtime = stops_df[outfield].max()

    # Add warnings here related to min and maxes out of whack with analysis range

    #

    analysis_range = [start_analysis_dt, end_analysis_dt]

    # Create date and range and convert it from a pandas DateTimeIndex to a
    # reqular old array of datetimes to try to get around the weird problems
    # in computing day of week on datetime64 values.
    # bin_freq = str(bin_size_minutes) + 'min'
    #rng_bydt = pd.date_range(start_date, end_date, freq=bin_freq).to_pydatetime()
    #rng_bydt = pd.date_range(start_date, end_date, freq=bin_freq)

    rng_bydt = pd.date_range(start_analysis_dt, end_analysis_dt, freq=Minute(bin_size_minutes))
    datebins = pd.DataFrame(index=rng_bydt)
    
    

    print ("rng_bydt created: {:.4f}".format(timer()-start))

    # import sys
    # sys.exit("Stopping after rng_bydt_list creation")
    #
    # num_days = (end_date-start_date).days + 1
    # num_periods = num_days * (1440//bin_size_minutes)
    # print(num_periods)
    #
    # # The following is no faster than the pandas date_range() method.
    # #rng_bydt = [start_date + timedelta(minutes=i*60) for i in range(num_periods)]
    # rng_int = [100 + i*60 for i in range(num_periods)]
    #
    # print ("rng_bydt list created: {}".format(time.clock()))




    # Get the unique category values or used passed in list
    if (not categories):
        categories = [c for c in stops_df[catfield].unique()]
        print ('using derived categories: {:.4f}'.format(timer()-start))
    else:
        stops_df = stops_df[stops_df[catfield].isin(categories)]
        print ('using specified categories: {:.4f}'.format(timer()-start))


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


    print ("Seeded bydatetime DataFrame created: {:.4f}".format(timer()-start))

    # Now create a hierarchical multiindex to replace the default index (since it
    # has dups from the concatenation). We keep the columns used in the index as
    # regular columns as well since it's hard
    # to do a column transformation using a specific level of a multiindex.
    # http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64?rq=1



    bydt_df['day_of_week'] = bydt_df['datetime'].map(lambda x: x.weekday())
    bydt_df['bin_of_day'] =  bydt_df['datetime'].map(lambda x: hm.bin_of_day(x,bin_size_minutes))
    bydt_df['bin_of_week'] = bydt_df['datetime'].map(lambda x: hm.bin_of_week(x,bin_size_minutes))

    print ("dayofweek, bin_of_day, bin_of_week computed: {:.4f}".format(timer()-start))


    bydt_df.set_index(['category', 'datetime'], inplace=True, drop=False)
    print ("Multi-index on bydatetime DataFrame created: {:.4f}".format(timer()-start))

    bydt_df.sortlevel(inplace=True)
    print ("Multi-index fully lexsorted: {:.4f}".format(timer()-start))
    
    # bydt_df.to_csv('after_lexsort.csv')
    # Main occupancy, arrivals, departures loop. Process each record in the
# stop data file.

    # The following "standard approach" is slow and very non-Pythonic
    # This

    #idx = pd.IndexSlice

    num_processed = 0
    num_inner = 0
    print ("Latest edits at {}".format(datetime.now()))

    rectype_counts = {}

    for intime_raw, outtime_raw, cat in zip(stops_df[infield],stops_df[outfield], stops_df[catfield]):
        intime = hm.to_the_second(intime_raw)
        outtime = hm.to_the_second(outtime_raw)
        good_rec = True
        rectype = hm.stoprec_analysis_rltnshp([intime,outtime],analysis_range)
    
        if rectype in ['backwards']:
            # print "ERROR_{}: {} {} {}".format(rectype,intime,outtime,cat)
            good_rec = False

            rectype_counts['backwards'] = rectype_counts.get('backwards',0) + 1
    
        if good_rec and rectype != 'none':
            indtbin =  hm.dt_floor(intime,bin_size_minutes)
            # i = datebins.index.searchsorted(intime)
            # if (intime == datebins.index[i]):
            #     indtbin = datebins.index[i]
            # else:
            #     indtbin = datebins.index[i-1]
            outdtbin =  hm.dt_floor(outtime,bin_size_minutes)
            # i = datebins.index.searchsorted(outtime)
            #
            # if (outtime == datebins.index[i]):
            #     outdtbin = datebins.index[i]
            # else:
            #     outdtbin = datebins.index[i-1]
            
            inout_occ_frac = hm.occ_frac([intime, outtime], bin_size_minutes)
            numbins = hm.numbins(indtbin, outdtbin, bin_size_minutes)
            dtbin = indtbin


            
            # print "{} {} {} {} {:.3f} {:.3f} {:.3f}".format(intime, outtime, cat,
            #    rectype, time.clock(), inout_occ_frac[0], inout_occ_frac[1])

            if rectype == 'inner':
                num_inner += 1
                rectype_counts['inner'] = rectype_counts.get('inner',0) + 1

                bydt_df.at[(cat,indtbin), 'occupancy'] += inout_occ_frac[0]
                bydt_df.at[(cat,indtbin), 'arrivals'] += 1.0
                bydt_df.at[(cat,outdtbin), 'departures'] += 1.0

                bin = 2
                while bin < numbins:
                    dtbin += timedelta(minutes=bin_size_minutes)
                    bydt_df.at[(cat,dtbin), 'occupancy'] += 1.0
                    bin += 1

                if numbins > 1:
                    bydt_df.at[(cat,outdtbin), 'occupancy'] += inout_occ_frac[1]

                # I'm counting on this being a copy
                #print(num_processed+1,cat,indtbin,outdtbin,numbins,inc_list)
                #print(DataFrame(bydt_df.loc[idx[[cat],indtbin:outdtbin],idx['occupancy']]))

                #inc_df = DataFrame(bydt_df.loc[idx[cat,indtbin:outdtbin],idx['occupancy']] + inc_list) # 169.5
                # inc_df = (bydt_df.loc[idx[cat,indtbin:outdtbin],idx['occupancy']] + inc_list) # 166.8
                # bydt_df.loc[idx[[cat],indtbin:outdtbin],idx['occupancy']] += inc_list # Error

                #The update takes the bulk of the time
                #bydt_df.update(inc_df)
    
            elif rectype == 'right':
                rectype_counts['right'] = rectype_counts.get('right',0) + 1
                # departure is outside analysis window
                bydt_df.at[(cat,indtbin), 'occupancy'] += inout_occ_frac[0]
                bydt_df.at[(cat,indtbin), 'arrivals'] += 1.0
    
                if hm.isgt2bins(indtbin, outdtbin, bin_size_minutes):
                    bin = indtbin + timedelta(minutes=bin_size_minutes)
                    while bin <= end_analysis_dt:
                        bydt_df.at[(cat,bin), 'occupancy'] += 1.0
                        bin += timedelta(minutes=bin_size_minutes)
    
            elif rectype == 'left':
                rectype_counts['left'] = rectype_counts.get('left',0) + 1
                # arrival is outside analysis window
                bydt_df.at[(cat,outdtbin), 'occupancy'] += inout_occ_frac[1]
                bydt_df.at[(cat,outdtbin), 'departures'] += 1.0
    
                if hm.isgt2bins(indtbin, outdtbin, bin_size_minutes):
                    bin = start_analysis_dt
                    while bin < outdtbin:
                        bydt_df.at[(cat,bin), 'occupancy'] += 1.0
                        bin += timedelta(minutes=bin_size_minutes)
    
            elif rectype == 'outer':
                rectype_counts['outer'] = rectype_counts.get('outer',0) + 1
                # arrival and departure sandwich analysis window
    
                if hm.isgt2bins(indtbin, outdtbin, bin_size_minutes):
                    bin = start_analysis_dt
                    while bin <= end_analysis_dt:
                        bydt_df.at[(cat,bin), 'occupancy'] += 1.0
                        bin += timedelta(minutes=bin_size_minutes)
    
            else:
                pass
    
            num_processed += 1
            #print numprocessed

    print("Num inner: {}".format(num_inner))
    print(rectype_counts)
    print ("Done processing {} stop recs: {:.4f}".format(num_processed, timer()-start))

    # Compute totals
    if(totals):
        bydt_group = bydt_df.groupby(['datetime'])

        tot_arrivals = bydt_group.arrivals.sum()
        tot_departures = bydt_group.departures.sum()
        tot_occ = bydt_group.occupancy.sum()

        tot_data = [tot_arrivals,tot_departures,tot_occ]
        tot_df = pd.concat(tot_data, axis = 1, keys = [s.name for s in tot_data])
        tot_df['day_of_week'] = tot_df.index.map(lambda x: x.weekday())
        tot_df['bin_of_day'] =  tot_df.index.map(lambda x: hm.bin_of_day(x,bin_size_minutes))
        tot_df['bin_of_week'] = tot_df.index.map(lambda x: hm.bin_of_week(x,bin_size_minutes))

        tot_df['category'] = total_str
        tot_df.set_index('category', append=True, inplace=True, drop=False)
        tot_df = tot_df.reorder_levels(['category', 'datetime'])
        tot_df['datetime'] = tot_df.index.levels[1]

        col_order = ['category','datetime','arrivals','departures','occupancy','day_of_week','bin_of_day','bin_of_week']
        tot_df = tot_df[col_order]
        bydt_df = bydt_df.append(tot_df)

        print ("Done adding totals: {:.4f}".format(timer()-start))


    return bydt_df




if __name__ == '__main__':

    file_stopdata = 'data/unit_stop_log_Experiment1_Scenario1_Rep1.csv'

    scenario_name = 'log_unitocc_test'
    in_fld_name = 'EnteredTS'
    out_fld_name = 'ExitedTS'
    cat_fld_name = 'Unit'
    start_analysis = '2/15/2015 00:00'
    end_analysis = '6/16/2016 00:00'

    # Optional inputs

    tot_fld_name = 'OBTot'
    bin_size_mins = 60
    includecats = ['LDR','PP']

    df = pd.read_csv(file_stopdata)
    basedate = Timestamp('20150215 00:00:00')
    df['EnteredTS'] = df.apply(lambda row: Timestamp(round((basedate + pd.DateOffset(hours=row['Entered'])).value,-9)), axis=1)
    df['ExitedTS'] = df.apply(lambda row: Timestamp(round((basedate + pd.DateOffset(hours=row['Exited'])).value,-9)), axis=1)

    bydt_df = make_bydatetime(df,in_fld_name, out_fld_name,cat_fld_name,
                                     start_analysis,end_analysis,
                                     tot_fld_name,bin_size_mins,categories=includecats)

    file_bydt_csv = 'testing/bydatetime_main_' + scenario_name + '.csv'
    file_bydt_pkl = 'testing/bydatetime_main_' + scenario_name + '.pkl'

    bydt_df.to_csv(file_bydt_csv)
    bydt_df.to_pickle(file_bydt_pkl)

