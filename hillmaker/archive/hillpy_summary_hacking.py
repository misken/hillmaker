# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 15:11:31 2012

@author: mark
"""
# General imports
import os

import numpy as np
import matplotlib.pyplot as plt

# Pandas setup
from pandas import DataFrame, Series
import pandas as pd

from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse

# Change directory into working HillPy dir
# Change directory into working HillPy dir
if os.name == 'nt':
    if os.getenv('COMPUTERNAME') == 'ISKEN_HP':
        os.chdir('C:\Users\isken\Dropbox\HillPy')
    else:
        os.chdir('C:\Users\mark\Dropbox\HillPy')
else:
    os.chdir('/home/mark/Dropbox/HillPy')

# HillPy setup
import hmlib

# Read sample data set and convert string dates to datetimes

bydate_df = pd.read_csv('bydate_proto_4.csv',parse_dates=['datetime'])



# Create a GroupBy object for the summary stats    
bydate_dfgrp1 = bydate_df.groupby(['category','bin_of_week'])
                                      

bydate_dfgrp1.mean().to_csv('group1.csv',float_format='%.3f')

bydate_dfgrp2 = bydate_df.groupby(['category','dayofweek','bin_of_day'])

# Here's a version with explicit cols and suppressed index                    
#bydate_dfgrp2 = bydate_df.groupby( \
#                    ['category','dayofweek','bin_of_day'],as_index=False) \
#                    ['occupancy','arrivals','departures']    

# Iterating over groups
#for (name1,name2,name3), group in bydate_dfgrp2:
#    print name1, name2, name3  # Will be key values in hierarchical index
#    print group # Will be rows of data in this group
    
bydate_dfgrp2.mean().to_csv('group2.csv',float_format='%.3f') 

occ_basic_dict = {'occupancy' : ['count','min','max','mean','std']}  

#bydate_dfgrp1.agg(occ_basic_dict)[0:25]

def get_occstats(group, stub=''):
    return {stub+'count': group.count(), stub+'mean': group.mean(), 
            stub+'min': group.min(),
            stub+'max': group.max(), 'stdev': group.std(), 
            stub+'p50': group.quantile(0.5), stub+'p55': group.quantile(0.55),
            stub+'p60': group.quantile(0.6), stub+'p65': group.quantile(0.65),
            stub+'p70': group.quantile(0.7), stub+'p75': group.quantile(0.75),
            stub+'p80': group.quantile(0.8), stub+'p85': group.quantile(0.85),
            stub+'p90': group.quantile(0.9), stub+'p95': group.quantile(0.95),
            stub+'p975': group.quantile(0.975), 
            stub+'p99': group.quantile(0.99)}

# Create a list of columns in desired order
          
# Let's create separate data frames for each 
occ = bydate_dfgrp2['occupancy'].apply(get_occstats).unstack()
arr = bydate_dfgrp2['arrivals'].apply(get_occstats).unstack()
dep = bydate_dfgrp2['departures'].apply(get_occstats).unstack()

cols = occ.columns.tolist()
newcols = cols[0:1] + cols[2:3] + cols[-1:0] + \
          cols[3:4] + cols[1:2] + cols[4:16]
          
occ = occ[newcols]
arr = arr[newcols]
dep = dep[newcols]

occ.to_csv('occ.csv')
arr.to_csv('arr.csv')
dep.to_csv('dep.csv')
#.unstack()[1:100]['mean'].values
#print bydate_dfgrp2['occupancy'].apply(get_stats).unstack()['ART'][:24]['mean']