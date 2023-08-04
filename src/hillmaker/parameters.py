from datetime import datetime, date
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, validator, BaseSettings, Field, confloat
from typing import Dict, List, Optional, Tuple, Union
from enum import IntEnum


class EdgeBinsEnum(IntEnum):
    FRACTIONAL = 1
    ENTIRE = 2


class VerbosityEnum(IntEnum):
    WARNING = 0
    INFO = 1
    DEBUG = 2


class Parameters(BaseModel):
    """pydantic model for input parameters

    Parameters
    ----------
    scenario_name : str
        Used in output filenames
    stops_df : DataFrame
        Base data containing one row per visit
    in_field : str
        Column name corresponding to the arrival times
    out_field : str
        Column name corresponding to the departure times
    start_analysis_dt : datetime-like, str
        Starting datetime for the analysis (must be convertible to pandas Timestamp)
    end_analysis_dt : datetime-like, str
        Ending datetime for the analysis (must be convertible to pandas Timestamp)
    cat_field : str, optional
        Column name corresponding to the categories. If none is specified, then only overall occupancy is summarized.
        Default is None
    bin_size_minutes : int, optional
        Number of minutes in each time bin of the day, default is 60. Use a value that
        divides into 1440 with no remainder
    cats_to_exclude : list, optional
        Category values to ignore, default is None
    occ_weight_field : str, optional
        Column name corresponding to the weights to use for occupancy incrementing, default is None
        which corresponds to a weight of 1.0.
    edge_bins: int, default 1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=entire bin
    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)
    totals: bool
        False=no totals, True=totals by datetime. Default is True.
    cap : int, optional
        Capacity of area being analyzed, default is None. Used only to add capacity line to occupancy plots.
    nonstationary_stats : bool, optional
       If True, datetime bin stats are computed. Else, they aren't computed. Default is True
    stationary_stats : bool, optional
       If True, overall, non-time bin dependent, stats are computed. Else, they aren't computed. Default is True
    adjust_censored_departures: bool, optional
       If True, missing departure datetimes are replaced with datetime of end of analysis range. If False,
       record is ignored. Default is False.
    export_bydatetime_csv : bool, optional
       If True, bydatetime DataFrames are exported to csv files. Default is True.
    export_summaries_csv : bool, optional
       If True, summary DataFrames are exported to csv files. Default is True.
    export_dow_png : bool, optional
       If True, day of week plots are exported for occupancy, arrival, and departure. Default is False.
    export_week_png : bool, optional
       If True, full week plots are exported for occupancy, arrival, and departure. Default is False.
    xlabel : str
        x-axis label, default='Hour'
    ylabel : str
        y-axis label, default='Occupancy'
    output_path : str or Path, optional
        Destination path for exported csv and png files, default is current directory
    verbosity : int, optional
        Used to set level in loggers. 0=logging.WARNING (default=0), 1=logging.INFO, 2=logging.DEBUG


    """

    # Required parameters
    scenario_name: str
    stops_df: pd.DataFrame
    in_field: str
    out_field: str
    start_analysis_dt: Union[date, datetime]
    end_analysis_dt: Union[date, datetime]
    # Optional parameters
    cat_field: str = None
    bin_size_minutes: int = 60
    cats_to_exclude: List[str] = None
    occ_weight_field: str = None
    percentiles: Union[Tuple[confloat(ge=0.0, le=1.0)], List[confloat(ge=0.0, le=1.0)]] = (0.25, 0.5, 0.75, 0.95, 0.99)
    totals: bool = True
    nonstationary_stats: bool = True
    stationary_stats: bool = True
    adjust_censored_departures: bool = False
    edge_bins: EdgeBinsEnum = EdgeBinsEnum.FRACTIONAL
    output_path: Union[str, Path] = Path('.')
    export_bydatetime_csv: bool = True
    export_summaries_csv: bool = True
    make_dow_plot: bool = True
    make_week_plot: bool = True
    export_dow_png: bool = False
    export_week_png: bool = False
    cap: int = None
    xlabel: str = 'Hour'
    ylabel: str = 'Patients'
    verbosity: int = VerbosityEnum.WARNING

    # Ensure required fields and submitted optional fields exist
    @validator('in_field', 'out_field', 'cat_field', 'occ_weight_field')
    def field_exists(cls, v, values):
        if v is not None and v not in values['stops_df'].columns:
            raise ValueError(f'{v} is not a column in the dataframe')
        return v

    # End date >= start date
    @validator('end_analysis_dt')
    def date_relationship(cls, v, values):
        if v < values['start_analysis_dt']:
            raise ValueError(f'end date must be >= start date')
        return v

    # Ensure bin_size_minutes divides into 1440 with no remainder
    @validator('bin_size_minutes')
    def bin_size_minutes_divides(cls, v):
        if 1440 % v > 0:
            raise ValueError('bin_size_minutes must divide into 1440 with no remainder')
        return v

    # def __str__(self):
    #     """Pretty string representation of scenario parameters"""
    #     # TODO - write str method for Scenario class
    #     return str(self)

    class Config:
        arbitrary_types_allowed = True
