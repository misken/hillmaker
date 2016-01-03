# -*- coding: utf-8 -*-
"""
Created on Wed Jan 02 13:19:51 2013

@author: mark
"""

# General imports
import math
import numpy as np
from datetime import datetime
from datetime import timedelta
import pandas as pd
from pandas import Timestamp
import time



class Hilltimer:
    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start


def td_to_mins(x):
    """
    Converts a timedelta object to minutes

    """

    num_secs = x * (10 ** (-9)) / 60.0
    return int(num_secs)



def bin_of_day(dt, bin_size_mins=30):
    """
    Computes bin of day based on bin size for a datetime.
    
    Parameters
    ----------
    dt : pandas Timestamp object or a Python datetime object, default now.
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
    if dt is None: 
        dt = datetime.now()
    # else:
    #     dt = Timestamp(dt)

    # YES, I know that type checking is NOT Pythonic!!!
    # However, the hell that is numpy.datetime64 data types has 
    # caused me to give up and do it anyway. 

    # if not isinstance(dt, datetime):
    #     dt = pd.Timestamp(dt)

    minutes = (dt.hour * 60) + dt.minute
    time_bin = math.trunc(minutes / bin_size_mins)
    return time_bin




def bin_of_week(dt, bin_size_mins=30):
    """
    Computes bin of week based on bin size for a datetim.
    
    Based on .weekday() convention of 0=Monday.
    
    Parameters
    ----------
    dt : pandas Timestamp object or a Python datetime object, default now.
    bin_size_mins : Size of bin in minutes; default 30 minutes.
    
    Returns
    -------
    0 to (n-1) where n is number of bins per week.
    
    Examples
    --------
    dt = datetime(2013,1,7,1,45)
    bin = bin_of_week(dt,30)
    # bin = ???

    """
    if dt is None:
        dt = datetime.now()

    minutes = (dt.weekday() * 1440) + (dt.hour * 60) + dt.minute
    time_bin = math.trunc(minutes / bin_size_mins)
    return time_bin


def dt_floor(dt, minutes):
    """
   Find floor of a datetime object to specified number of minutes.
   
   dt : Pandas Timestamp object
   floor_minutes : Closest number of minutes to round to.
    :rtype: Timestamp
   """

    floor_seconds = minutes * 60
    dt_date = Timestamp(dt.date())
    delta = dt - dt_date
    # #print(delta)
    tot_seconds = delta.total_seconds()
    # #print(tot_seconds)
    #
    floor_time = (tot_seconds // floor_seconds) * floor_seconds
    # #print(floor_time)
    # #gap_seconds = tot_seconds - floor_time
    # #print(dt_date + pd.DateOffset(seconds=floor_time))
    return dt_date + pd.DateOffset(seconds=floor_time)
    #return dt + timedelta(0, floor_time - tot_seconds, -dt.microsecond)

def dt_floor_exp(dt, binsizemins=60):
    """Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
            Stijn Nevens 2014 - Changed to use only datetime objects as variables
    """
    dateDelta=timedelta(minutes=binsizemins)
    roundTo = dateDelta.total_seconds()


    totseconds = (dt - dt.min).seconds
    # // is a floor division, not a comment on following line:
    rounding = (totseconds // roundTo) * roundTo
    return dt + timedelta(0,rounding-totseconds, -dt.microsecond)

def dt_ceiling(dt, minutes):
    """
   Find ceiling of a datetime object to specified number of minutes
   
   dt : datetime.datetime object
   roundMinsTo : Closest number of minutes to round to.
   """
    ceiling_seconds = minutes * 60.0
    seconds = timedelta_to_seconds(dt - dt.min)

    ceiling_time = math.ceil(seconds / ceiling_seconds) * ceiling_seconds
    return dt + timedelta(0, ceiling_time - seconds, -dt.microsecond)


def isgt2bins(indtbin, outdtbin, binsize_mins):
    return (outdtbin - indtbin) > timedelta(minutes=binsize_mins)

def numbins(indtbin, outdtbin, binsize_mins):
    return 1 + (timedelta_to_seconds(outdtbin - indtbin)/60.0) / binsize_mins

def to_the_second(ts):
    return Timestamp(round(ts.value, -9))
    
def timedelta_to_seconds(td):
    #return td.days*86400 + td.hours*3600 + td.minutes*60 + td.seconds
    return td.total_seconds()
    
def occ_frac(stoprecrange, binsize_mins, rectype='inner'):
    """
    Computes fractional occupancy in inbin and outbin.
    
    Parameters
    ----------
    stoprecrange: list consisting of [intime, outtime]
    binsize_mins: bin size in minutes
    rectype: One of'inner', 'outer', 'left', 'right'. See 
             stoprec_analysis_rltnshp() doc for details.

    Returns
    -------   
    [inbin frac, outbin frac] where each is a real number in [0.0,1.0]
    
    """

    intime = stoprecrange[0]
    outtime = stoprecrange[1]

    indtbin = dt_floor(intime, binsize_mins)
    outdtbin = dt_floor(outtime, binsize_mins)

    # inbin occupancy
    rightedge = min(indtbin + timedelta(minutes=binsize_mins), outtime)
    inbin_occ_secs = timedelta_to_seconds(rightedge - intime)
    inbin_occ_frac = inbin_occ_secs / (binsize_mins * 60.0)

    # outbin occupancy
    if indtbin == outdtbin:
        outbin_occ_frac = 0.0  # Use inbin_occ_frac
    else:
        leftedge = max(outdtbin, intime)
        outbin_occ_secs = timedelta_to_seconds(outtime - leftedge)
        outbin_occ_frac = outbin_occ_secs / (binsize_mins * 60.0)

    assert inbin_occ_frac <= 1.0 and inbin_occ_frac >= 0.0, \
        "bad inbin_occ_frac={:.3f} in={} out={}".format(inbin_occ_frac,
                                                        intime, outtime)

    assert outbin_occ_frac <= 1.0 and outbin_occ_frac >= 0.0, \
        "bad outbin_occ_frac={:.3f} in={} out={}".format(outbin_occ_frac,
                                                         intime, outtime)

    return [inbin_occ_frac, outbin_occ_frac]


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
