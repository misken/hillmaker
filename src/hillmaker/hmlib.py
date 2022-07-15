# Copyright 2022 Mark Isken

import math
from datetime import datetime
from datetime import timedelta
import time

import numpy as np
from pandas import Timestamp


def bin_of_day(dt, bin_size_mins=30):
    """
    Compute bin of day based on bin size for a datetime.
    
    Parameters
    ----------
    dt : pandas Timestamp object or a Python datetime object, default now.
    bin_size_mins : Size of bin in minutes; default 30 minutes.
    
    Returns
    -------
    0 to (n-1) where n is number of bins per day.
    
    Examples
    --------
    dt = datetime(2013,1,7,1,45)
    bin = bin_of_day(dt, 30)
    # bin = 3

    """
    if dt is None:
        dt = datetime.now()

    # Number of minutes from beginning of day
    minutes = (dt.hour * 60) + dt.minute
    # Convert minutes to bin
    time_bin = math.trunc(minutes / bin_size_mins)
    return time_bin


def bin_of_week(dt, bin_size_mins=30):
    """
    Compute bin of week based on bin size for a pandas Timestamp object
    or a Python datetime object.
    
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
    dt = datetime(2020, 2, 4, 1, 45)
    bin = bin_of_week(dt, 30)
    # bin = 51
    """
    # if dt is None:
    #     dt = datetime.now()

    # Number of minutes from beginning of week (Monday is 0)
    minutes = (dt.weekday() * 1440) + (dt.hour * 60) + dt.minute
    # Convert minutes to bin
    time_bin = math.trunc(minutes / bin_size_mins)
    return time_bin


def isgt2bins(indtbin, outdtbin, bin_size_minutes):
    """
    Returns True if occupancy spans more than 2 bins.

    Parameters
    ----------
    indtbin
    outdtbin
    bin_size_minutes

    Returns
    -------
    bool
    """

    return (outdtbin - indtbin) > timedelta(minutes=bin_size_minutes)


def num_bins(indtbin, outdtbin, bin_size_minutes):
    """
    Compute number of bins for which partial or full occupancy contributions exist.

    Parameters
    ----------
    indtbin
    outdtbin
    bin_size_minutes

    Returns
    -------
    Number of bins
    """
    tot_seconds = (outdtbin - indtbin).total_seconds()
    return 1 + (tot_seconds / 60.0) / bin_size_minutes


def occ_frac(stop_rec_range, bin_size_minutes, edge_bins=1):
    """
    Computes fractional occupancy in inbin and outbin.

    Parameters
    ----------
    stop_rec_range: list consisting of [intime, outtime]
    bin_size_minutes: bin size in minutes
    edge_bins: 1=fractional, 2=whole bin

    Returns
    -------
    [inbin frac, outbin frac] where each is a real number in [0.0,1.0]

    """
    intime = stop_rec_range[0]
    outtime = stop_rec_range[1]

    bin_freq_str = '{}T'.format(int(bin_size_minutes))
    indtbin = intime.floor(bin_freq_str)
    outdtbin = outtime.floor(bin_freq_str)

    # inbin occupancy
    if edge_bins == 1:
        right_edge = min(indtbin + timedelta(minutes=bin_size_minutes), outtime)
        inbin_occ_secs = (right_edge - intime).total_seconds()
        inbin_occ_frac = inbin_occ_secs / (bin_size_minutes * 60.0)
    else:
        inbin_occ_frac = 1.0

    # outbin occupancy
    if indtbin == outdtbin:
        outbin_occ_frac = 0.0  # Use inbin_occ_frac
    else:
        if edge_bins == 1:
            left_edge = max(outdtbin, intime)
            outbin_occ_secs = (outtime - left_edge).total_seconds()
            outbin_occ_frac = outbin_occ_secs / (bin_size_minutes * 60.0)
        else:
            outbin_occ_frac = 1.0

    assert 1.0 >= inbin_occ_frac >= 0.0, \
        "bad inbin_occ_frac={:.3f} in={} out={}".format(inbin_occ_frac,
                                                        intime, outtime)

    assert 1.0 >= outbin_occ_frac >= 0.0, \
        "bad outbin_occ_frac={:.3f} in={} out={}".format(outbin_occ_frac,
                                                         intime, outtime)

    return [inbin_occ_frac, outbin_occ_frac]


def stoprec_analysis_rltnshp(in_dt, out_dt, start_span, end_span):
    """
    Determines relationship type of stop record to analysis date range.
    
    Parameters
    ----------


    Returns
    -------   
    Returns a str, either 'inner', 'left', 'right, 'outer',
    'backwards', or 'none' depending on the relationship between
    the stop record being analyzed and the analysis date range.
    
    Type 'inner':
        
         |-------------------------|
     start_analysis                  end_analysis
              |--------------|
             in_dt         out_dt
             
    Type 'left':
        
                    |-------------------------|
                  start_analysis                end_analysis
              |--------------|
             in_dt         out_dt
             
    Type 'right':
        
                    |-------------------------|
                  start_analysis                end_analysis
                                       |--------------|
                                     in_dt         out_dt
             
    Type 'outer':
        
              |-------------------------|
            start_analysis                end_analysis
       |-------------------------------------|
     in_dt                              out_dt   
     
    
    Type 'backwards':
        The exit time is BEFORE the entry time. This is a BAD record.
    
    Type 'none':
        Ranges do not overlap
    """

    if in_dt > out_dt:
        return 'backwards'
    elif (start_span <= in_dt < end_span) and (start_span <= out_dt < end_span):
        return 'inner'
    elif (start_span <= in_dt < end_span) and (out_dt >= end_span):
        return 'right'
    elif (in_dt < start_span) and (start_span <= out_dt < end_span):
        return 'left'
    elif (in_dt < start_span) and (out_dt >= end_span):
        return 'outer'
    else:
        return 'none'


def bin_of_analysis_range(dt, start_analysis_range, bin_size_mins=60):
    """
    Compute bin of span of analysis based on bin size for a datetime.

    Bins are closed on the left boundary.

    Parameters
    ----------
    dt : array of numpy timedelta64
    bin_size_mins : Size of bin in minutes; default 30 minutes.

    Returns
    -------
    array of integer <= (n-1) where n is number of bins in span of analysis.

    Examples
    --------
    start = datetime(1996, 1, 1, 1, 0)
    dt = datetime(1996, 3, 1, 14, 30)
    bin = bin_of_span(dt, 600)

    """

    # Number of minutes from beginning of span
    minutes = (dt - start_analysis_range).astype('timedelta64[s]') / 60.0
    minutes = minutes.astype(np.int64)
    # Convert minutes to bin
    time_bin = np.floor(minutes / bin_size_mins).astype(np.int64)

    return time_bin


class HillTimer:

    def __enter__(self):
        self.start = time.process_time()
        return self

    def __exit__(self, *args):
        self.end = time.process_time()
        self.interval = self.end - self.start
