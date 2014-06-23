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

import pyodbc

# Pandas setup
from pandas import DataFrame, Series
import pandas as pd

from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import pandas.io.sql as sql


# Change directory into working HillPy dir
if os.name == 'nt':
    if os.getenv('COMPUTERNAME') == 'ISKEN_HP':
        os.chdir('C:\Users\isken\Dropbox\HillPy')
    else:
        os.chdir('C:\Users\mark\Dropbox\HillPy')
else:
    os.chdir('/home/mark/Dropbox/HillPy')
    
# HillPy setup
import hillpylib as hlib
    
# Input parameters
file_stopdata_csv = 'data/ShortStay.csv'
file_stopdata_xlsx = 'data/ShortStay.xlsx'
file_stopdata_mdb = 'C:\\Users\\mark\\Dropbox\\HillPy\\data\\ShortStay.mdb'
file_stopdata_accdb = 'C:\\Users\\mark\\Dropbox\\HillPy\\data\\ShortStay.accdb'
scenario_name = 'proto_4'
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
#df = pd.read_csv(file_stopdata,parse_dates=[in_fld_name,out_fld_name])

#xlsx_file = pd.ExcelFile(file_stopdata_xlsx)
#df = xlsx_file.parse('ShortStay',parse_dates=True)
#Provider=Microsoft.Jet.OLEDB.4.0;Data Source=C:\\Users\\mark\\Dropbox\\HillPy\\data\\ShortStay.mdb;

connection_string = 'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+file_stopdata_accdb

cn = pyodbc.connect(connection_string)
df = sql.read_frame('select * from tblShortStay',cn)

# Compute LOS
df['LOS'] = df[out_fld_name] - df[in_fld_name]
df['LOSmins'] = hlib.vtd_to_mins(df['LOS'])

# Create seeded by date table
bin_freq = str(binsize_mins) + 'min'
rng_bydate = pd.date_range(start_analysis_dt, end_analysis_dt, freq=bin_freq)
len_bydate = len(rng_bydate)


# Get the unique category values
categories = [c for c in df[cat_fld_name].unique()]

columns=['category','datetime','arrivals','departures','occupancy']
         
# Create and empty ByDate data frame

bydate_df = DataFrame(columns=columns)
                                           

for cat in categories:
    bydate_data = {'category':[cat]*len_bydate,
                   'datetime':rng_bydate,
                   'arrivals':[0.0]*len_bydate,
                   'departures':[0.0]*len_bydate,
                   'occupancy':[0.0]*len_bydate,
                   }

    bydate_df_cat = DataFrame(bydate_data,columns=['category',
                                           'datetime',
                                           'arrivals',
                                           'departures',
                                           'occupancy'])
                                           
    bydate_df = pd.concat([bydate_df,bydate_df_cat])

# Now create a hierarchical index to replace the default index (since it
# has dups from the concatenation). We keep the columns used in the index as
# regular columns as well since it's hard
# to do a column transformation using a specific level of a multiindex.
# http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64?rq=1

bydate_df = bydate_df.set_index(['category', 'datetime'], drop=False)





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

# Compute totals for arrivals, departures and occupancy by using
# Pandas aggregation methods
    
bydate_dfgrp1 = bydate_df.groupby(level='datetime') \
                                  ['occupancy','arrivals','departures']    

bydate_tot = bydate_dfgrp1.sum() # Compute the totals
bydate_tot.reset_index(inplace=True)  # Moves the index column to a data column
bydate_tot['category'] = cat_total_str  # Set the category for the total rows

# Set the index to conform to the main bydate data frame. The inplace=True
# avoids creating a new object
bydate_tot.set_index(['category','datetime'], inplace=True, drop=False)
    
# Concatenate the totals to the main data frame
bydate_df = pd.concat([bydate_df,bydate_tot])


  
## Write out bydate_df to csv to examine it. Suppress the index. This should
## look like a typical Hillmaker seeded ByDate table.

#    
## print bydate_df.values    
#    
# 
#    
## Fill in dayofweek, bin_of_day, and bin_of_week columns to facilitate agg
## stats. 
#
bydate_df['dayofweek'] = 0
bydate_df['dayofweek'] = bydate_df['datetime'].apply(lambda x: x.astype(datetime).weekday())
bydate_df['bin_of_day'] = 0
bydate_df['bin_of_week'] = 0

for cat, dt in izip(bydate_df['category'], bydate_df['datetime']):
    dow = dt.weekday()
    bofd = hlib.bin_of_day(dt,binsize_mins)
    bofw = hlib.bin_of_week(dt,binsize_mins)
    bydate_df.ix[(cat,dt), 'dayofweek'] = dow
    bydate_df.ix[(cat,dt), 'bin_of_day'] = bofd
    bydate_df.ix[(cat,dt), 'bin_of_week'] = bofw
#    
del bydate_df['category']  
del bydate_df['datetime']

bydate_df.to_csv('bydate_' + scenario_name + '.csv')  
    
    
     