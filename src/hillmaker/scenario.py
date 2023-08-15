from datetime import datetime, date
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple, Union
from enum import IntEnum

import pandas as pd
from pydantic import BaseModel, field_validator, model_validator, confloat, FieldValidationInfo, ConfigDict
import hillmaker as hm

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

# This should inherit level from root logger
logger = logging.getLogger(__name__)


class EdgeBinsEnum(IntEnum):
    FRACTIONAL = 1
    ENTIRE = 2


class VerbosityEnum(IntEnum):
    WARNING = 0
    INFO = 1
    DEBUG = 2


class Scenario(BaseModel):
    """pydantic model for creating scenario objects from input parameters

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
    export_bydatetime_csv : bool, optional
       If True, bydatetime DataFrames are exported to csv files. Default is True.
    export_summaries_csv : bool, optional
       If True, summary DataFrames are exported to csv files. Default is True.
    make_dow_plot : bool, optional
       If True, day of week plots are created for occupancy, arrival, and departure. Default is True.
    make_week_plot : bool, optional
       If True, full week plots are created for occupancy, arrival, and departure. Default is True.
    export_dow_plot : bool, optional
       If True, day of week plots are exported for occupancy, arrival, and departure. Default is False.
    export_week_plot : bool, optional
       If True, full week plots are exported for occupancy, arrival, and departure. Default is False.
    xlabel : str
        x-axis label, default='Hour'
    ylabel : str
        y-axis label, default='Occupancy'
    output_path : str or Path, optional
        Destination path for exported csv and png files, default is current directory
    verbosity : int, optional
        Used to set level in loggers. 0=logging.WARNING (default=0), 1=logging.INFO, 2=logging.DEBUG

    Attributes
    ----------
    hills : dict (initialized to None)
        Stores results of `make_hills`.


    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Required parameters
    scenario_name: str
    stops_df: pd.DataFrame
    in_field: str
    out_field: str
    # TODO - what if a pandas Timestamp or numpy datetime64 is passed in?
    # See https://github.com/pydantic/pydantic/discussions/6972
    start_analysis_dt: date | datetime | pd.Timestamp
    end_analysis_dt: date | datetime | pd.Timestamp
    # Optional parameters
    cat_field: str = None
    bin_size_minutes: int = 60
    cats_to_exclude: List[str] | None = None
    occ_weight_field: str | None = None
    percentiles: Tuple[confloat(ge=0.0, le=1.0)] | List[confloat(ge=0.0, le=1.0)] = (0.25, 0.5, 0.75, 0.95, 0.99)
    nonstationary_stats: bool = True
    stationary_stats: bool = True
    edge_bins: EdgeBinsEnum = EdgeBinsEnum.FRACTIONAL
    output_path: str | Path = Path('.')
    export_bydatetime_csv: bool = True
    export_summaries_csv: bool = True
    make_dow_plot: bool = True
    make_week_plot: bool = True
    export_dow_plot: bool = False
    export_week_plot: bool = False
    cap: int | None = None
    xlabel: str | None = 'Hour'
    ylabel: str | None = 'Patients'
    verbosity: int = VerbosityEnum.WARNING
    hills: dict | None = None

    # Ensure required fields and submitted optional fields exist
    @field_validator('in_field', 'out_field', 'cat_field', 'occ_weight_field')
    def field_exists(cls, v: str, info: FieldValidationInfo):
        if v is not None and v not in info.data['stops_df'].columns:
            raise ValueError(f'{v} is not a column in the dataframe')
        return v

    @field_validator('end_analysis_dt')
    def date_relationship(cls, v: str, info: FieldValidationInfo):
        if v <= info.data['start_analysis_dt']:
            raise ValueError(f'end date must be > start date')
        return v

    # Ensure bin_size_minutes divides into 1440 with no remainder
    @field_validator('bin_size_minutes')
    def bin_size_minutes_divides(cls, v: int):
        if 1440 % v > 0:
            raise ValueError('bin_size_minutes must divide into 1440 with no remainder')
        return v

    def make_hills(self):
        """
        Wrapper for module level `hillmaker.make_hills()` function.

        Returns
        -------
        dict stored in `hills` attribute of Scenario object

        """
        # Get dict version of pydantic model
        inputs_dict = self.model_dump()
        # Remove output related attributes
        inputs_dict.pop('hills', None)
        # Pass remaining parameters to hillmaker.make_hills()
        self.hills = hm.make_hills(**inputs_dict)
        # return self

    def get_plot(self, flow_metric: str = 'occupancy', day_of_week: str = 'week'):
        """
        Get plot object for specified flow metric and whether full week or specified day of week.

        Parameters
        ----------
        flow_metric : str
            Either of 'arrivals', 'departures', 'occupancy' ('a', 'd', and 'o' are sufficient).
            Default='occupancy'
        day_of_week : str
            Either of 'week', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'. Default='week'

        Returns
        -------
        plot object from matplotlib

        """

        plot = hm.hills.get_plot(self.hills, flow_metric, day_of_week)
        return plot

    def get_summary_df(self, flow_metric: str = 'occupancy',
                       by_category: bool = True, stationary: bool = False):
        """
        Get summary dataframe

        Parameters
        ----------
        flow_metric : str
            Either of 'arrivals', 'departures', 'occupancy' ('a', 'd', and 'o' are sufficient).
            Default='occupancy'
        by_category : bool
            Default=True corresponds to category specific statistics. A value of False gives overall statistics.
        stationary : bool
            Default=False corresponds to the standard nonstationary statistics (i.e. by TOD and DOW)

        Returns
        -------
        DataFrame

        """
        df = hm.hills.get_summary_df(self.hills, flow_metric='o', by_category=by_category, stationary=stationary)
        return df

    def get_bydatetime_df(self, by_category: bool = True):
        """
        Get bydatetime dataframe

        Parameters
        ----------
        by_category : bool
            Default=True corresponds to category specific statistics. A value of False gives overall statistics.


        Returns
        -------
        DataFrame

        """
        df = hm.hills.get_bydatetime_df(self.hills, by_category=by_category)
        return df

    def __str__(self):
        """Pretty string representation of a scenario"""
        # TODO - write str method for Scenario class
        return str(self.model_dump())


def create_scenario(params_dict: Optional[Dict] = None,
                    toml_path: Optional[str | Path] = None, **kwargs):
    """Function to create a `Scenario` from a dict, a TOML file, and/or keyword args """

    # Create empty dict for input parameters
    params = {}

    # If params_dict is not None, merge into params
    if params_dict is not None:
        params.update(params_dict)

    # If params_path is not None, merge into params
    if toml_path is not None:
        with open(toml_path, "rb") as f:
            params_toml_dict = tomllib.load(f)
            params.update(params_toml_dict)

    # Args passed to function get ultimate say
    if len(kwargs) > 0:
        params.update(kwargs)

    # Now, from the params dictionary, create pydantic Parameters model
    # Be nice to construct model so that some default values
    # can be based on app settings
    # Get application settings
    # app_settings: Settings = Settings()

    # Create Pydantic model to parse and validate inputs
    scenario = Scenario(**params)

    return scenario
