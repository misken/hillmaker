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


# HillPy setup
import hillpylib as hlib

# Change directory into working HillPy dir
if os.name == 'nt':
    if os.getenv('COMPUTERNAME') == 'ISKEN_HP':
        os.chdir('C:\Users\isken\Dropbox\HillPy')
    else:
        os.chdir('C:\Users\mark\Dropbox\HillPy')
else:
    os.chdir('/home/mark/Dropbox/HillPy')
    
# Input parameters
file_stopdata = 'ShortStay.csv'
cat_fld_name = 'PatType' # NOT USED
in_fld_name = 'InTime'
out_fld_name = 'OutTime'
binsize_mins = 60
start_analysis = '3/1/1996'
end_analysis = '8/4/1996 23:00'

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

bydate_data = {'arrivals':[0]*len_bydate,
               'departures':[0]*len_bydate,
               'occupancy':[0.0]*len_bydate}

bydate_df = DataFrame(bydate_data, index=rng_bydate)

for intime, outtime in izip(df[in_fld_name], df[out_fld_name]):
    rectype = hlib.stoprec_analysis_rltnshp([intime,outtime],analysis_range)
    
    if rectype != 'none':
        indtbin = hlib.rounddownTime(intime,binsize_mins)
        outdtbin = hlib.rounddownTime(outtime,binsize_mins)
        inout_occ_frac = hlib.occ_frac([intime, outtime], binsize_mins)
        print intime, outtime, rectype, time.clock(), inout_occ_frac
        
        if rectype == 'inner':
            bydate_df.ix[indtbin, 'occupancy'] += inout_occ_frac[0]
            bydate_df.ix[outdtbin, 'occupancy'] += inout_occ_frac[1]
            bydate_df.ix[indtbin, 'arrivals'] += 1.0
            bydate_df.ix[outdtbin, 'departures'] += 1.0
            
            if hlib.isgt2bins(indtbin, outdtbin, binsize_mins):
                bin = indtbin + timedelta(minutes=binsize_mins)
                while bin < outdtbin:
                    bydate_df.ix[bin, 'occupancy'] += 1.0
                    bin += timedelta(minutes=binsize_mins)
                    
    
        elif rectype == 'right':
            # departure is outside analysis window
            bydate_df.ix[indtbin, 'occupancy'] += inout_occ_frac[0]        
            bydate_df.ix[indtbin, 'arrivals'] += 1.0
                   
            if hlib.isgt2bins(indtbin, outdtbin, binsize_mins):
                bin = indtbin + timedelta(minutes=binsize_mins)
                while bin <= end_analysis_dt:
                    bydate_df.ix[bin, 'occupancy'] += 1.0
                    bin += timedelta(minutes=binsize_mins)
                    
        elif rectype == 'left':
            # arrival is outside analysis window
            bydate_df.ix[outdtbin, 'occupancy'] += inout_occ_frac[1]        
            bydate_df.ix[outdtbin, 'departures'] += 1.0
                   
            if hlib.isgt2bins(indtbin, outdtbin, binsize_mins):
                bin = start_analysis_dt + timedelta(minutes=binsize_mins)
                while bin < outdtbin:
                    bydate_df.ix[bin, 'occupancy'] += 1.0
                    bin += timedelta(minutes=binsize_mins)
        
        elif rectype == 'outer':
            # arrival and departure sandwich analysis window
                   
            if hlib.isgt2bins(indtbin, outdtbin, binsize_mins):
                bin = start_analysis_dt
                while bin <= end_analysis_dt:
                    bydate_df.ix[bin, 'occupancy'] += 1.0
                    bin += timedelta(minutes=binsize_mins)
        
        else:
            pass

    
    
    
# Write out bydate_df to csv to examine it. Suppress the index. This should
# look like a typical Hillmaker seeded ByDate table.
bydate_df.to_csv('bydate_proto_2.csv')
    
print bydate_df.values    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    