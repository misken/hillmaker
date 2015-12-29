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

# Pandas setup
from pandas import DataFrame, Series
import pandas as pd

from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse


# HillPy setup
import hmlib

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
binsize_mins = 30
start_analysis = '2/1/1996'
end_analysis = '5/4/1996 23:00'
    
# Read sample data set and convert string dates to datetimes
df = pd.read_csv(file_stopdata,parse_dates=[in_fld_name,out_fld_name])


# Compute LOS
df['LOS'] = df[out_fld_name] - df[in_fld_name]
df['LOSmins'] = hmlib.vtd_to_mins(df['LOS'])

# Create seeded by date table
bin_freq = str(binsize_mins) + 'min'
rng_bydate = pd.date_range(start_analysis, end_analysis, freq=bin_freq)

bydate_data = {'arrivals':[0]*len(rng_bydate),
               'departures':[0]*len(rng_bydate),
               'occupancy':[0.0]*len(rng_bydate)}

bydate_df = DataFrame(bydate_data, index=rng_bydate)

for intime, outtime in izip(df[in_fld_name], df[out_fld_name]):
    print intime, outtime
    indtbin = hmlib.rounddownTime(intime)
    outdtbin = hmlib.rounddownTime(outtime)
    
    inbin_occ_secs = (indtbin + timedelta(minutes=30) - intime).seconds
    inbin_occ = inbin_occ_secs/(30.0*60.0)
    
    outbin_occ_secs = (outtime - outdtbin).seconds
    outbin_occ = outbin_occ_secs/(30.0*60.0)
    
    occbinrng = pd.date_range(indtbin, outdtbin, freq=bin_freq)
    
    # I'm guessing it's slow to create these objects repeatedly
    occ_data = {'arrivals':[0]*len(occbinrng),
                'departures':[0]*len(occbinrng),
                'occupancy':[0.0]*len(occbinrng)}

    occ_df = DataFrame(occ_data, index=occbinrng)
    
    occ_df.ix[indtbin, 'arrivals'] = 1.0
    occ_df.ix[outdtbin, 'departures'] = 1.0
    occ_df['occupancy'] = 1.0
    occ_df.ix[indtbin, 'occupancy'] = inbin_occ
    occ_df.ix[outdtbin, 'occupancy'] = outbin_occ
    
    bydate_df = bydate_df.add(occ_df, fill_value=0)
    
bydate_df.to_csv('bydate_proto_2.csv')

print bydate_df.values    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    