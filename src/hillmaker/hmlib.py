# Copyright 2022 Mark Isken

import math
from datetime import datetime
from datetime import timedelta
import time
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

import numpy as np
from pandas import Timestamp


def bin_of_day(dt: Union[Timestamp, datetime], bin_size_mins: int = 60):
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


def bin_of_week(dt: Union[Timestamp, datetime], bin_size_mins: int = 60):
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



def stoprec_analysis_rltnshp(in_dt: Union[Timestamp, datetime],
                             out_dt: Union[Timestamp, datetime],
                             start_analysis: Union[Timestamp, datetime],
                             end_analysis: Union[Timestamp, datetime]):
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
    elif (start_analysis <= in_dt < end_analysis) and (start_analysis <= out_dt < end_analysis):
        return 'inner'
    elif (start_analysis <= in_dt < end_analysis) and (out_dt >= end_analysis):
        return 'right'
    elif (in_dt < start_analysis) and (start_analysis <= out_dt < end_analysis):
        return 'left'
    elif (in_dt < start_analysis) and (out_dt >= end_analysis):
        return 'outer'
    else:
        return 'none'


def bin_of_analysis_range(dt: Union[Timestamp, datetime],
                          start_analysis_range: Union[Timestamp, datetime],
                          bin_size_mins: int = 60):
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

def toml_to_flatdict(toml_filepath: Union[str, Path]):
    """Convert toml input parameters file to flat dictionary"""
    with open(toml_filepath, mode="rb") as toml_file:
        params_toml = tomllib.load(toml_file)

    flat_dict = pd.json_normalize(params_toml, max_level=1)
    # Fix up key names
    for key, val in flat_dict.items():
        if '.' in key:
            new_key = key.split('.',)[1]
            flat_dict[new_key] = val
            del flat_dict[key]

    return flat_dict.iloc[0].to_dict()