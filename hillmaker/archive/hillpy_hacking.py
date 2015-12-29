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
df = pd.read_csv('ShortStay.csv',parse_dates=['InTime','OutTime'])
cat_name = 'PatType'

dfByDate = pd.read_csv('tblByDate_ShortStay1.csv',
                       parse_dates=['TheDateTime'])



# List columns
print df

# See some rows

print df.head()            # First five
print df.tail(10)          # Last ten
print df[1:10]             # All the c# Change directory into working HillPy dir
print df[cat_name][1:10]  # Just a specific column

# List rows from a specific column
print df.InTime
print df['OutTime']

# Compute LOS in new column - SURPRISINGLY HARD
#df['LOS'] = 0.0 # assigning value to new column creates new col in df

df['LOStd'] = df['OutTime'] - df['InTime']

# Get name, values and data type for the new column
print df['LOStd'].name
print df['LOStd'].values
print df['LOStd'].dtype

# Creates a Series of timedelta objects. Getting it in hours should be as simple
# as df['LOS1'] = (df['OutTime'] - df['InTime'].days * 24. However, pandas
# won't let you get at the days attribute for an entire Series of timedeltas. It's
# as if it's not vectorized.
# Turns out to be hard to get things like hours from a Series of timedelta objects
# http://stackoverflow.com/questions/12405677/get-days-property-from-numpy-ndarray-of-timedelta-objects
# Wrote a quick function, td_to_mins(), and a companion vectorizer to do the work.
df['LOSmins'] = hmlib.vtd_to_mins(df['LOStd'])

# Now let's try with list comp. It works.

df['LOSmins_lstcmp'] = [hmlib.td_to_mins(df['LOStd'][i]) for i in range(len(df))]

df['LOSmins'].quantile(0.75)


# Do some aggregations

grouped = dfByDate['Arrivals'].groupby(dfByDate['PatType'])
grouped.mean()
grouped.quantile(0.7)

groupedFull = dfByDate.groupby(['PatType','BinOfWeek'])['Arrivals']
groupedFull_alt = dfByDate['Arrivals'].groupby([dfByDate['PatType'],dfByDate['BinOfWeek']]) # More verbose

groupedFull.mean()
groupedFull.quantile(0.7)


#Now create a separate series object
sLOS = Series(df['LOStd'])

# Create a group of histograms
#plt.figure();df['LOSmins'].hist(by=df['PatType'])

# Count number of patients by patient type

#### Creating and initializing a seeded ByDate table

rng = pd.date_range('1/1/1996', '3/31/1996 23:00', freq='H')

# Get the unique category values
categories = [c for c in df[cat_name].unique()]

# Create the ByDate dataframe using _Total for category. We will concatenate the category specific
# records next.
bydate_data = {'category':['_Total']*len(rng),
               'datetime':rng,
               'arrivals':[0]*len(rng),
               'departures':[0]*len(rng),
               'occupancy':[0.0]*len(rng)}

bydate_df = DataFrame(bydate_data,columns=['category','datetime','arrivals','departures','occupancy'])

for cat in categories:
    bydate_data = {'category':[cat]*len(rng),
               'datetime':rng,
               'arrivals':[0]*len(rng),
               'departures':[0]*len(rng),
               'occupancy':[0.0]*len(rng)}

    bydate_df_cat = DataFrame(bydate_data,columns=['category','datetime','arrivals','departures','occupancy'])

    bydate_df = pd.concat([bydate_df,bydate_df_cat])

# Now create a hierarchical index to replace the default index (since it
# has dups from the concatenation). For now we'll leave the base cols in
# as well for convenience.

bydate_df = bydate_df.set_index(['category', 'datetime'], drop=False)

# Access a specific category - first 10 rows of ART by date bins
print bydate_df.xs('ART')[0:10]

# Write out bydate_df to csv to examine it. Suppress the index. This should
# look like a typical Hillmaker seeded ByDate table.
bydate_df.to_csv('bydate_test.csv',index=False)

# Figuring out how to compute occupancy

intime = datetime(2013,1,7,8,30)
outtime = datetime(2013,1,8,10,45)

los = outtime - intime
los  # datetime.timedelta(1, 8100)

indate = intime.date() # Get a date object from a datetime obj

# Compute in and out time bins
df['indtbin'] = hmlib.vrounddownTime(df['InTime'])
df['outdtbin'] = hmlib.vrounddownTime(df['OutTime'])

for d in rng:
    print d