# -*- coding: utf-8 -*-
"""
Created on Wed Jan  2 22:53:32 2013

Ignores category field. Just tries to loop through records and update
by date table and compute occupancy stats.

@author: mark
"""

# General imports
import os

import numpy as np
import matplotlib.pyplot as plt
from itertools import izip
import time

# Pandas setup
from pandas import DataFrame, Series
import pandas as pd

from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse


# Change directory into working HillPy dir
if os.name == 'nt':
    if os.getenv('COMPUTERNAME') == 'ISKEN_HP':
        os.chdir('C:\Users\isken\Dropbox\HillPy')
    else:
        os.chdir('C:\Users\mark\Dropbox\HillPy')
else:
    os.chdir('/home/mark/Dropbox/HillPy')
    
# HillPy setup
import hmlib as hlib
    
# Input parameters
file_stopdata = 'ShortStay.csv'
scenario_name = 'proto_3'
cat_fld_name = 'PatType'
cat_total_str = '_Total' 
in_fld_name = 'InTime'
out_fld_name = 'OutTime'
binsize_mins = 60
start_analysis = '3/1/1996'
end_analysis = '4/4/1996 23:00'

start_analysis_dt = parse(start_analysis)
end_analysis_dt = parse(end_analysis)
analysis_range = [start_analysis_dt,end_analysis_dt]
    
# Read sample data set and convert string dates to datetimes
df = pd.read_csv(file_stopdata,parse_dates=[in_fld_name,out_fld_name])


# Compute LOS
df['LOS'] = df[out_fld_name] - df[in_fld_name]
df['LOSmins'] = hlib.vtd_to_mins(df['LOS'])

# Create seeded by date table
bin_freq = str(binsize_mins) + 'min'
rng_bydate = pd.date_range(start_analysis_dt, end_analysis_dt, freq=bin_freq)
len_bydate = len(rng_bydate)


# Get the unique category values
categories = [c for c in df[cat_fld_name].unique()]

columns=['category','datetime','arrivals','departures','occupancy', \
                                           'dayofweek',
                                           'bin_of_day',
                                           'bin_of_week']
# Create the ByDate dataframe using _Total for category. We will concatenate the category specific
# records next.
#DayType,TheWeekDay,BinOfDay,BinOfWeek
bydate_data = {'category':[cat_total_str]*len_bydate,
               'datetime':rng_bydate,
               'arrivals':[0]*len_bydate,
               'departures':[0]*len_bydate,
               'occupancy':[0.0]*len_bydate,
               'dayofweek':[0]*len_bydate,
               'bin_of_day':[0]*len_bydate,
               'bin_of_week':[0]*len_bydate}

bydate_df = DataFrame(bydate_data,columns=['category',
                                           'datetime',
                                           'arrivals',
                                           'departures',
                                           'occupancy',
                                           'dayofweek',
                                           'bin_of_day',
                                           'bin_of_week'])
                                           

for cat in categories:
    bydate_data = {'category':[cat]*len_bydate,
                   'datetime':rng_bydate,
                   'arrivals':[0]*len_bydate,
                   'departures':[0]*len_bydate,
                   'occupancy':[0.0]*len_bydate,
                   'dayofweek':[0]*len_bydate,
                   'bin_of_day':[0]*len_bydate,
                   'bin_of_week':[0]*len_bydate}

    bydate_df_cat = DataFrame(bydate_data,columns=['category',
                                           'datetime',
                                           'arrivals',
                                           'departures',
                                           'occupancy',
                                           'dayofweek',
                                           'bin_of_day',
                                           'bin_of_week'])
                                           
    bydate_df = pd.concat([bydate_df,bydate_df_cat])

# Now create a hierarchical index to replace the default index (since it
# has dups from the concatenation). We keep the columns used in the index as
# regular columns as well since it's hard
# to do a column transformation using a specific level of a multiindex.
# http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64?rq=1

bydate_df = bydate_df.set_index(['category', 'datetime'], drop=False)

# Fill in dayofweek, bin_of_day, and bin_of_week columns to facilitate agg
# stats. 

bydate_df['dayofweek'] = bydate_df['datetime'].apply(lambda x: x.astype(datetime).weekday())

for cat, dt in izip(bydate_df['category'], bydate_df['datetime']):
    dow = dt.weekday()
    bofd = hlib.bin_of_day(dt,binsize_mins)
    bofw = hlib.bin_of_week(dt,binsize_mins)
    bydate_df.ix[(cat,dt), 'dayofweek'] = dow
    bydate_df.ix[(cat,dt), 'bin_of_day'] = bofd
    bydate_df.ix[(cat,dt), 'bin_of_week'] = bofw

# The following vectorized funcs return incorrect results. Not sure why.
#bydate_df['bin_of_day'] = hlib.vbinofday(bydate_df['datetime'],binsize_mins)
#bydate_df['bin_of_week'] = hlib.vbinofweek(bydate_df['datetime'],binsize_mins)

# Main occupancy, arrivals, departures loop. Process each record in the 
# stop data file.

for intime, outtime, cat in izip(df[in_fld_name], df[out_fld_name], df[cat_fld_name]):
    rectype = hlib.stoprec_analysis_rltnshp([intime,outtime],analysis_range)
    
    if rectype != 'none':
        indtbin = hlib.rounddownTime(intime,binsize_mins)
        outdtbin = hlib.rounddownTime(outtime,binsize_mins)
        inout_occ_frac = hlib.occ_frac([intime, outtime], binsize_mins)
        print intime, outtime, cat, rectype, time.clock(), inout_occ_frac
        
        if rectype == 'inner':
            bydate_df.ix[(cat,indtbin), 'occupancy'] += inout_occ_frac[0]
            bydate_df.ix[(cat,outdtbin), 'occupancy'] += inout_occ_frac[1]
            bydate_df.ix[(cat,indtbin), 'arrivals'] += 1.0
            bydate_df.ix[(cat,outdtbin), 'departures'] += 1.0
            
            if hlib.isgt2bins(indtbin, outdtbin, binsize_mins):
                bin = indtbin + timedelta(minutes=binsize_mins)
                while bin < outdtbin:
                    bydate_df.ix[(cat,bin), 'occupancy'] += 1.0
                    bin += timedelta(minutes=binsize_mins)
                    
    
        elif rectype == 'right':
            # departure is outside analysis window
            bydate_df.ix[(cat,indtbin), 'occupancy'] += inout_occ_frac[0]        
            bydate_df.ix[(cat,indtbin), 'arrivals'] += 1.0
                   
            if hlib.isgt2bins(indtbin, outdtbin, binsize_mins):
                bin = indtbin + timedelta(minutes=binsize_mins)
                while bin <= end_analysis_dt:
                    bydate_df.ix[(cat,bin), 'occupancy'] += 1.0
                    bin += timedelta(minutes=binsize_mins)
                    
        elif rectype == 'left':
            # arrival is outside analysis window
            bydate_df.ix[(cat,outdtbin), 'occupancy'] += inout_occ_frac[1]        
            bydate_df.ix[(cat,outdtbin), 'departures'] += 1.0
                   
            if hlib.isgt2bins(indtbin, outdtbin, binsize_mins):
                bin = start_analysis_dt + timedelta(minutes=binsize_mins)
                while bin < outdtbin:
                    bydate_df.ix[(cat,bin), 'occupancy'] += 1.0
                    bin += timedelta(minutes=binsize_mins)
        
        elif rectype == 'outer':
            # arrival and departure sandwich analysis window
                   
            if hlib.isgt2bins(indtbin, outdtbin, binsize_mins):
                bin = start_analysis_dt
                while bin <= end_analysis_dt:
                    bydate_df.ix[(cat,bin), 'occupancy'] += 1.0
                    bin += timedelta(minutes=binsize_mins)
        
        else:
            pass

    
    
    
# Write out bydate_df to csv to examine it. Suppress the index. This should
# look like a typical Hillmaker seeded ByDate table.
bydate_df.to_csv('bydate_' + scenario_name + '.csv')
    
# print bydate_df.values    
    
# Create a GroupBy object for the summary stats    
   
    
bydate_dfgrp1 = bydate_df.groupby(level='datetime') \
                                  ['occupancy','arrivals','departures']    


bydate_tot = bydate_dfgrp1.sum()
bydate_tot.reset_index(inplace=True)  # Moves the index column to a data column
bydate_tot['category'] = cat_total_str  # Set the category for the total rows

# Set the index to conform to the main bydate data frame. The inplace=True
# avoids creating a new object
bydate_tot.set_index(['category','datetime'], inplace=True)


bydate_dfgrp1.sum().to_csv('group1.csv',float_format='%.3f')
    
bydate_dfgrp2 = bydate_df.groupby( \
                    ['category','dayofweek','bin_of_day'],as_index=False) \
                    ['occupancy','arrivals','departures']    
    
bydate_dfgrp2.mean().to_csv('group2.csv',float_format='%.3f')    
    
    
bydate_dfgrp1.sum()['occupancy'].head()    
    
    
    
    