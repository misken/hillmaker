# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #Computing occupancy statistics with Python - Part 1 of 3#
# Many years ago I created an MS Access add-in called Hillmaker for doing time of day and day of week based occupancy analysis in health care delivery systems. A typical use would be to find the mean and 95th percentile of occupancy in a set of nursing units or an emergency department. [Hillmaker](http://sourceforge.net/projects/hillmaker/) was released as an open source project back in 2005 and has gotten quite a bit of use. However, I never really did any more development on it even though there were a number of enhancements that I (and many others) would like to have seen. The only attention it has gotten from me was in response to the object library problems caused by new releases of MS Office. No fun.
# 
# While VBA is fine, I've always wanted to make Hillmaker less MS-centric and to decouple it from MS Access. Installing Access add-ins can be a hassle as they require changes to the Windows registry and some corporate settings frown on this. So, I hacked together a proof of concept version using Python with the pandas module for some of the number crunching and with matplotlib for plotting. Seems to work. Seems to be fast. Made it work with text files, Excel, Access and SQL Server based data. For this tutorial, I'll call it HillPy.
# 
# In this tutorial I'll focus on the basic ideas behind computing occupancy statistics with Python. The data is fictitious data from a hospital short stay unit. Patients flow through a short stay unit for a variety of procedures, tests or therapies. Let's assume patients can be classified into one of five categories of patient types: ART (arterialgram), CAT (post cardiac-cath), MYE (myelogram), IVT (IV therapy), and OTH (other).  From one of our hospital information systems we were able to get raw data about the entry and exit times of each patient. For simplicity, the data is in a csv file. Let's start by importing a bunch of modules we'll need.

# <markdowncell>

# ##Preliminaries##

# <codecell>

## General imports
from itertools import izip

import pandas as pd
import numpy as np
from pandas import Series, DataFrame
from datetime import datetime
from datetime import timedelta

## Import datetime related moudles
#from datetime import datetime
#from datetime import timedelta
#from dateutil.parser import parse
import time


# <markdowncell>

# I created a module to house some functions specific to HillPy. The details will be discussed when we encounter these functions.

# <codecell>

## HillPy library
import hmlib as hlib

# <markdowncell>

# The original Hillmaker application has a bunch of key input parameters. For this demo, I'm just going to hard code them.

# <codecell>

## Input parameters - just hard coding them for demonstration purposes

## The name of the csv file containing the raw stop record data
file_stopdata = 'data/ShortStay.csv'

## A string scenario identifier. It gets appended to output filenames.
scenario_name = 'shortstay_csv'

## The field in the raw data file corresponding to the category by which statistics are computed.
cat_fld_name = 'PatType'

## A string used as the category name for the overall total occupancy statistics.
cat_total_str = 'Total'

## The field in the raw data file with the timestamp of the patient entry time.
in_fld_name = 'InRoomTS'

## The field in the raw data file with the timestamp of the patient exit time.
out_fld_name = 'OutRoomTS'

## Each day is broken up into time bins. This is the bin size in minutes. Typical
## values are 15, 30, 60, 120, 240, or 480.
binsize_mins = 30

## We need a date range for the analysis. More on this below.
start_analysis = '1/2/1996'
end_analysis = '3/31/1996 23:45'
## Convert string dates to actual datetimes
start_analysis_dt = pd.Timestamp(start_analysis)
end_analysis_dt = pd.Timestamp(end_analysis)
analysis_range = [start_analysis_dt,end_analysis_dt]

# <markdowncell>

# ##The stop records##

# <markdowncell>

# It's important that you choose an analysis date range for which you have no missing data. It's also important to take system 'warm up' issues into account. This issue is discussed in a paper I wrote a bunch of years ago:
# 
# Isken, M.W. (2002) “Modeling and Analysis of Occupancy Data: A Healthcare Capacity Planning Application,”
# International Journal of Information Technology and Decision Making, 1, 4 (December) 707-729.
# 
# For this example it's not a big deal since length of stay is on the order of a few hours and many of the patients are scheduled during the standard business day.
# 
# Let's read in the raw "stop records" from a csv file. We refer to them as stop records since each row is a single stop (with associated entry and exit timestamps) by a single patient.

# <codecell>

## Read sample data set and convert string dates to datetimes
df = pd.read_csv(file_stopdata,parse_dates=[in_fld_name,out_fld_name])

# <codecell>

df.info()

# <codecell>

print type(df['InRoomTS'][0])
print type(df['OutRoomTS'][0])

# <codecell>

df.head()

# <codecell>

df.tail()

# <markdowncell>

# While we don't need to compute length of stay to do the occupancy analysis, let's do it anyway. We usually want to do descriptive statistics on length of stay.

# <markdowncell>

# Now for something totally evil.

# <codecell>

## Compute LOS - the results is a timedelta value
df['LOS'] = df[out_fld_name] - df[in_fld_name]

## Compute LOS in minutes using one of the functions in hillpylib
#df['LOSmins'] = hlib.vtd_to_mins(df['LOS'])

print type(df['LOS'][0])

# <markdowncell>

# Why is this a numpy.timedelta64 instead of a pandas timedelta? What's the difference between this example and the example I did in exploring_datetimes.ipynb? [http://stackoverflow.com/questions/23961287/preventing-pandas-from-coercing-datetime-timedelta-to-numpy-timedelta64-during-s](http://stackoverflow.com/questions/23961287/preventing-pandas-from-coercing-datetime-timedelta-to-numpy-timedelta64-during-s)

# <codecell>

lostest = df['LOS'][0]

# <codecell>

lostest.astype(int64)

# <codecell>

## Compute LOS - the results is a timedelta value
testlos = df[out_fld_name][0] - df[in_fld_name][0]

## Compute LOS in minutes using one of the functions in hillpylib
#df['LOSmins'] = hlib.vtd_to_mins(df['LOS'])

print type(testlos)

# <codecell>

# Let's just do the time time math
df['LOSmins'] = df['LOS'].map(lambda x: x.astype(int64)*(10**(-9))/60.0)

# <codecell>

reload(hlib)

# <codecell>

df['LOSmins2'] = hlib.vtd_to_mins(df['LOS'])

# <codecell>

df.head()

# <markdowncell>

# Here's what the relevant functions from hillpylib look like:

# <codecell>

import numpy as np
import pandas as pd

def td_to_mins(x):
    """
    Converts a timedelta object to minutes
    """
    return x.astype(int64)*(10**(-9)) / 60.0

vtd_to_mins = np.vectorize(td_to_mins) # Make usable with list like things

# <markdowncell>

# ##Creating a seeded *by date* table for occupancy, arrivals, and departures##
# Now we are ready for the main computational tasks of computing occupancy for every datetime bin and category (PatType in this example) in the analysis date range. In addition to computing occupancy, we'll also count the number of patient arrivals and departures in each datetime bin. Historically, this table is called the *by date* table (even though it's really by datetime bin by category. Our strategy is to first create a "fully seeded" table and then fill in the values by processing the raw patient stop records. By fully seeded we mean that there is a record for each combination of datetime bin and category value in the analysis date range and all of the measures (occupancy, arrivals, and departures) are initialized to 0. Let's start by creating the fully seeded table.

# <codecell>

# Create date and range and convert it from a pandas DateTimeIndex to a
# reqular old array of datetimes to try to get around the weird problems
# in computing day of week on datetime64 values.
bin_freq = str(binsize_mins) + 'min'
rng_bydate = pd.date_range(start_analysis_dt, end_analysis_dt,
                           freq=bin_freq).to_pydatetime()

# <codecell>

rng_bydate

# <markdowncell>

# Now let's create a list of the unique category values (the PatType column in this example).

# <codecell>

# Get the unique category values
categories = [c for c in df[cat_fld_name].unique()]
categories

# <markdowncell>

# Create a list of column names for the by date table and then an empty data frame based on these columns.

# <codecell>

columns=['category','datetime','arrivals','departures','occupancy']
# Create an empty ByDate data frame
bydate_df = DataFrame(columns=columns)

# <markdowncell>

# Now we'll build up the seeded by date table a category at a time. Along the way we'll initialize all the measures to 0.

# <codecell>

len_bydate = len(rng_bydate)
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

# <codecell>

bydate_df.head()

# <codecell>

bydate_df.tail()

# <markdowncell>

# Notice that each row in `bdate_df` corresponds to a half-hour time bin for a specific PatType (category). It's not readily apparent that we have created duplicate index values in the default pandas index. 

# <codecell>

bydate_df[4315:4330]

# <codecell>

# Now create a hierarchical multiindex to replace the default index (since it
# has dups from the concatenation). We keep the columns used in the index as
# regular columns as well since it's hard
# to do a column transformation using a specific level of a multiindex.
# http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64?rq=1

bydate_df = bydate_df.set_index(['category', 'datetime'], drop=False)

# <codecell>

bydate_df

# <codecell>

bydate_df[4315:4330]

# <markdowncell>

# Again, for now we aren't dropping the redundant **category** and **datetime** columns. We are going to compute three additional columns based on the value of **datetime** and it's easier to do such transformations on a regular data frame column than on a specific level of a multi-index. The three columns we want to add are:
# 
#  - day of week - 0..6 with 0=Monday
#  - bin of day - 0..(num_bins_per_day-1) where num_bins_per_day=48 if binsize_mins=30, num_bins_per_day=24 if binsize_mins=60, etc.
#  - bin of week - 0..(num_bins_per_week-1) where num_bins_per_week = 7 * num_bins_per_day
# 
# There is a built in `weekday()` function for datetimes. For bin of day and bin of week, we created custom functions in hillpylib. Notice the avoidance of loops via the use of `map()` and a lambda function.

# <codecell>

bydate_df['dayofweek'] = bydate_df['datetime'].map(lambda x: x.weekday())
bydate_df['bin_of_day'] =  bydate_df['datetime'].map(lambda x: hlib.bin_of_day(x,binsize_mins))
bydate_df['bin_of_week'] = bydate_df['datetime'].map(lambda x: hlib.bin_of_week(x,binsize_mins))

# <markdowncell>

# Instead of lambda functions, I did try to use vectorized versions of bin_of_day and bin_of_week, but pandas didn't seem to like them. Here are the bin of day and week functions:

# <codecell>

def binofday(dt, binsizemins):
    """
    Computes bin of day based on bin size for a datetime.
    
    Parameters
    ----------
    dt : datetime.datetime object, default now.
    binsizemins : Size of bin in minutes; default 30 minutes.
    
    Returns
    -------
    0 to (n-1) where n is number of bins per day.
    
    Examples
    --------
    dt = datetime(2013,1,7,1,45)
    bin = bin_of_day(dt,30)
    # bin = 3

    """
    if dt == None: dt = datetime.now()
    
    # YES, I know that type checking is NOT Pythonic!!!
    # However, the hell that is numpy.datetime64 data types has 
    # caused me to give up and do it anyway. 
    
    if not isinstance(dt,datetime):
        dt = pd.Timestamp(dt)
    
    mins = (dt.hour * 60) + dt.minute   
    bin = math.trunc(mins/binsizemins)
    return bin
 
  
def binofweek(dt, binsizemins):
    """
    Computes bin of week based on bin size for a datetime.
    
    Based on .weekday() convention of 0=Monday.
    
    Parameters
    ----------
    dt : datetime.datetime object, default now.
    binsizemins : Size of bin in minutes; default 30 minutes.
    
    Returns
    -------
    0 to (n-1) where n is number of bins per week.
    
    Examples
    --------
    dt = datetime(2013,1,9,1,45)
    bin = bin_of_week(dt,30)
    # bin = 99

    """
    if dt == None: dt = datetime.now()
    
    # YES, I know that type checking is NOT Pythonic!!!
    # However, the hell that is numpy.datetime64 data types has 
    # caused me to give up and do it anyway. 
    
    if not isinstance(dt,datetime):
        dt = pd.Timestamp(dt)
    
    mins = (dt.weekday() * 1440) + (dt.hour * 60) + dt.minute
    bin = math.trunc(mins/binsizemins)
    return bin

# <codecell>

bydate_df.head()

# <markdowncell>

# ## Arrival and departure bins and occupancy contributions ##
# A few more preliminary concepts are needed before we can churn the crank and process the stop records and fill in the bydate table with occupancy, arrival, and departure info.
# 
# Let's look at the first few stop records.

# <codecell>

df.head()

# <codecell>

df['InRoomTS'][0]  # Entry time for first record

# <codecell>

df['OutRoomTS'][0] # Exit time for first record

# <markdowncell>

# So, the first patient arrived in the 30 minute time bin beginning on 1996-01-01 07:30:00 and departed during the bin beginning 1996-01-01 08:30:00. We call 1996-01-01 07:30:00 the *arrival bin* and 1996-01-01 08:30:00 the *departure bin*. The first patient was in the system for all or part of 3 time bins:
# 
#  - 1996-01-01 07:30:00 - 1996-01-01 08:00:00 (16 mins --> 16/30 = 0.5333 of bin is the *arrival bin fraction*)
#  - 1996-01-01 08:00:00 - 1996-01-01 08:30:00 (30 mins --> 30/30 = 1.0000 of bin)
#  - 1996-01-01 08:30:00 - 1996-01-01 09:00:00 (20 mins --> 20/30 = 0.6667 of bin is the *departure bin fraction*)
# 
# The standard convention in Hillmaker is to use the arrival (departure) bin fraction as the contribution to occupancy in the arrival (departure) bin. For all bins between the arrival and departure bins, the patient is in the system for the entire bin length and thus the contribution to occupancy for each bin is 1.0. If you want to be more conservative, you could give full credit of 1.0 for the arrival and departure bins (this is an option in Hillmaker).
# 
# So, it seems we just need to step through all the rows in the stop record data frame, `df`, and:
# 
#  - get the PatType value
#  - find the arrival and departure bins
#  - compute the arrival and departure bin fractions, 
#  - and increment the appropriate rows in the `bydate_df` data frame.

# <markdowncell>

# ## Stop record types ##
# Well, it's almost that easy. There's one more complication to deal with. Recall that as part of the input parameters we specified start and end dates for the analysis (the *analysis date range*):
# 
# `start_analysis = '1/2/1996'`
# 
# `end_analysis = '3/31/1996 23:45'`
# 
# Obviously, a patient stop record having an arrival time after `end_analysis` can be ignored as can those patients who departed before `start_analysis`. For those patients whose stop falls strictly between `start_analysis` and `end_analysis`, they will end up with occupancy contributions for all of the time bins corresponding to their stay. However, what about patients who arrive during the analysis date range but depart after `end_analysis` or those who arrive before `start_analysis` and depart within the analysis date range. As you'd expect, we simply ignore time bins that fall outside of the analysis date range. Note we are NOT ignoring the entire record. We are simply computing occupancy contributions only for time bins falling within the analysis date range. To make our life easier, we created a function to determine the *stop record type*. You'll see in the comments below the function declaration that there is a diagram illustrating the different record types.

# <codecell>

def stoprec_analysis_rltnshp(stoprecrange, analysisrange):
    """
    Determines relationship type of stop record to analysis date range.
    
    Parameters
    ----------
    stoprecrange: list consisting of [rec_in, rec_out]
    analysisrange: list consisting of [a_start, a_end]

    Returns
    -------   
    Returns a string, either 'inner', 'left', 'right, 'outer', 
    'backwards', 'none' depending
    on the relationship between the stop record being analyzed and the
    analysis date range.
    
    Type 'inner':
        
         |-------------------------|
     a_start                     a_end
              |--------------|
             rec_in         rec_out
             
    Type 'left':
        
                    |-------------------------|
                  a_start                     a_end
              |--------------|
             rec_in         rec_out
             
    Type 'right':
        
                    |-------------------------|
                  a_start                     a_end
                                       |--------------|
                                     rec_in         rec_out
             
    Type 'outer':
        
              |-------------------------|
            a_start                     a_end
       |-------------------------------------|
     rec_in                              rec_out   
     
    
    Type 'backwards':
        The exit time is BEFORE the entry time. This is a BAD record.
    
    Type 'none':
        Ranges do not overlap
    """
    rec_in = stoprecrange[0]
    rec_out = stoprecrange[1]
    a_start = analysisrange[0]
    a_end = analysisrange[1]
    
    if (rec_in > rec_out):
        return 'backwards'
    elif (a_start <= rec_in < a_end) and (a_start <= rec_out < a_end):
        return 'inner'
    elif (a_start <= rec_in < a_end) and (rec_out >= a_end):
        return 'right'
    elif (rec_in < a_start) and (a_start <= rec_out < a_end):
        return 'left'
    elif (rec_in < a_start) and (rec_out >= a_end):
        return 'outer'
    else:
        return 'none'

# <markdowncell>

# ##Main processing loop##
# Finally, we can step through the patient stop records and fill in the by date table.

# <codecell>

reload(hlib)

# <codecell>

# Main occupancy, arrivals, departures loop. Process each record in the
# stop data file.

numprocessed = 0
for intime, outtime, cat in izip(df[in_fld_name], df[out_fld_name], df[cat_fld_name]):
    good_rec = True
    rectype = hlib.stoprec_analysis_rltnshp([intime,outtime],analysis_range)

    if rectype in ['backwards']:
        # print "ERROR_{}: {} {} {}".format(rectype,intime,outtime,cat)
        good_rec = False

    if good_rec and rectype != 'none':
        indtbin = hlib.rounddownTime(intime,binsize_mins)
        #print indtbin
        outdtbin = hlib.rounddownTime(outtime,binsize_mins)
        inout_occ_frac = hlib.occ_frac([intime, outtime], binsize_mins)
        # print "{} {} {} {} {:.3f} {:.3f} {:.3f}".format(intime, outtime, cat,
        #    rectype, time.clock(), inout_occ_frac[0], inout_occ_frac[1])

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
        
        numprocessed += 1
        #print numprocessed

print "Done processing {} stop recs: {}".format(numprocessed, time.clock())

# <markdowncell>

# At this point, `bydate_df` contains occupancy, arrival and departure counts for each time bin and category. Here's a look into the heart of the by date table.

# <codecell>

import time

# <codecell>

bydate_df[1320:1350]

# <markdowncell>

# ##Computing totals##
# Before computing statistics such as means and percentiles, we compute the total (over all categories) occupancy, arrivals and departures by time bin.

# <codecell>

# Compute totals for arrivals, departures and occupancy by using
# Pandas aggregation methods
bydate_dfgrp1 = bydate_df.groupby(level='datetime') ['occupancy','arrivals','departures']
bydate_tot = bydate_dfgrp1.sum() # Compute the totals

bydate_tot.reset_index(inplace=True)  # Moves the index column to a data column
bydate_tot['category'] = cat_total_str  # Set the category for the total rows

# Set the index to conform to the main bydate data frame. The inplace=True
# avoids creating a new object
bydate_tot.set_index(['category','datetime'], inplace=True, drop=False)

# Concatenate the totals to the main data frame
bydate_df = pd.concat([bydate_df,bydate_tot])

# Update dayofweek, bin_of_day, bin_of_week
bydate_df['dayofweek'][bydate_df['category'] == "Total"] = bydate_df['datetime'][bydate_df['category'] == "Total"].map(lambda x: pd.Timestamp(x).weekday())
bydate_df['bin_of_day'][bydate_df['category'] == 'Total'] =  bydate_df['datetime'][bydate_df['category'] == "Total"].map(lambda x: hlib.bin_of_day(x,binsize_mins))
bydate_df['bin_of_week'][bydate_df['category'] == 'Total'] = bydate_df['datetime'][bydate_df['category'] == "Total"].map(lambda x: hlib.bin_of_week(x,binsize_mins))

# Drop the redundant category and datetime fields (since they comprise the multi-index)
del bydate_df['category']
del bydate_df['datetime']

# Look at the tail to see example of totals
bydate_df.tail()

# <markdowncell>

# Write out `bydate_df` to a csv file and take a look at it. With this data frame we can compute all kinds of interesting summary statistics by day of week and time of day. That will be the subject of part 2 of this tutorial.

# <codecell>

file_bydate_csv = 'bydate_' + scenario_name + '.csv'
bydate_df.to_csv(file_bydate_csv)

# <markdowncell>

# ### About this IPython notebook ###
# You can download a zip file containing the data, the `.ipynb` file, and a `.py` version for this tutorial.
# 
# - [hillpy_bydate_demo.zip](https://github.com/misken/hselab-tuts-files.git)
# 
# Check out the [IPython doc on the notebook format](http://ipython.org/ipython-doc/stable/interactive/htmlnotebook.html#the-notebook-format) to learn all about working with
# IPython notebooks. A few highlights include:
# 
# - IPython notebooks are JSON text files with a `.ipynb` extension.
# - You can download a notebook as regular `.py` file with a **File|Download As...** and setting the download filetype to py.
# - If you add the proper comments to a regular `.py` file, you can open it as a notebook file by dragging and dropping the file into the notebook dashboard file list area. See
# the doc link above for the details on how to comment your Python file so that this works well.
# - To create a static HTML or PDF of your notebook, do a **File|Print** and then just save or print or whatever from the resulting browser window.

# <codecell>


