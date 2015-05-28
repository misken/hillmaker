# -*- coding: utf-8 -*-
"""
Demo of creation of the "by date" table for doing occupancy analysis. This
version is just a code listing meant to accompany the blog post



@author: mark isken
"""

# General imports
from itertools import izip
import time
from datetime import timedelta
from dateutil.parser import parse

# Pandas setup
from pandas import DataFrame
import pandas as pd

# HillPy setup
import hillpylib as hlib

# Input parameters
file_stopdata_csv = 'medhome_sample_startstop.txt'
scenario_name = 'medhome_demo'
cat_fld_name = 'mcpprovidername'
cat_total_str = 'Total'
in_fld_name = 'pcmassigneddate'
out_fld_name = 'stop_date'
binsize_mins = 1440
start_analysis = '1/1/2010'
end_analysis = '1/1/2011'
sep="\t"

start_analysis_dt = parse(start_analysis)
end_analysis_dt = parse(end_analysis)
analysis_range = [start_analysis_dt,end_analysis_dt]


file_bydate_csv = 'bydate_' + scenario_name + '.csv'

# Read sample data set and convert string dates to datetimes
df = pd.read_csv(file_stopdata_csv,parse_dates=[in_fld_name,out_fld_name],sep=sep)

# Compute LOS
df['LOS'] = df[out_fld_name] - df[in_fld_name]
df['LOSmins'] = hlib.vtd_to_mins(df['LOS'])

# Create seeded by date table


# Create date and range and convert it from a pandas DateTimeIndex to a
# reqular old array of datetimes to try to get around the weird problems
# in computing day of week on datetime64 values.
bin_freq = str(binsize_mins) + 'min'
rng_bydate = pd.date_range(start_analysis_dt, end_analysis_dt,
                           freq=bin_freq).to_pydatetime()
len_bydate = len(rng_bydate)


# Get the unique category values
categories = [c for c in df[cat_fld_name].unique()]

columns=['category','datetime','arrivals','departures','occupancy']

# Create an empty ByDate data frame
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


bydate_df['dayofweek'] = bydate_df['datetime'].map(lambda x: x.weekday())
bydate_df['bin_of_day'] = \
    bydate_df['datetime'].map(lambda x: hlib.bin_of_day(x,binsize_mins))
bydate_df['bin_of_week'] = \
    bydate_df['datetime'].map(lambda x: hlib.bin_of_week(x,binsize_mins))

# Main occupancy, arrivals, departures loop. Process each record in the
# stop data file.

for intime, outtime, cat in izip(df[in_fld_name], df[out_fld_name], df[cat_fld_name]):
    good_rec = True
    rectype = hlib.stoprec_analysis_rltnshp([intime,outtime],analysis_range)

    if rectype in ['backwards']:
        print "ERROR_{}: {} {} {}".format(rectype,intime,outtime,cat)
        good_rec = False

    if good_rec and rectype != 'none':
        indtbin = hlib.rounddownTime(intime,binsize_mins) # Arrival bin
        outdtbin = hlib.rounddownTime(outtime,binsize_mins) # Departure bin
        inout_occ_frac = hlib.occ_frac([intime, outtime], binsize_mins)
        print "{} {} {} {} {:.3f} {:.3f} {:.3f}".format(intime, outtime, cat,
            rectype, time.clock(), inout_occ_frac[0], inout_occ_frac[1])

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
print "Done computing dow, bod, bow: {}".format(time.clock())

bydate_df.to_csv(file_bydate_csv)

print "By date table: {}. Run time: {}".format(file_bydate_csv,time.clock())


