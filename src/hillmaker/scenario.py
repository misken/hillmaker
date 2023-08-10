from datetime import datetime, date
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple, Union
from enum import IntEnum

import pandas as pd
from pydantic import BaseModel, field_validator, model_validator, confloat, FieldValidationInfo, ConfigDict

from hillmaker import make_hills

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


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
    cats_to_exclude: List[str] = None        if self.start_analysis_dt > self.end_analysis_dt:
            raise ValueError(
                f'end date {self.end_analysis_dt} is before start date {self.start_analysis_dt}')
    occ_weight_field: str = None
    percentiles: Tuple[confloat(ge=0.0, le=1.0)] | List[confloat(ge=0.0, le=1.0)] = (0.25, 0.5, 0.75, 0.95, 0.99)
    totals: bool = True
    nonstationary_stats: bool = True
    stationary_stats: bool = True
    adjust_censored_departures: bool = False
    edge_bins: EdgeBinsEnum = EdgeBinsEnum.FRACTIONAL
    output_path: str | Path = Path('.')
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
    @field_validator('in_field', 'out_field', 'cat_field', 'occ_weight_field')
    def field_exists(cls, v: str, info: FieldValidationInfo):
        if v is not None and v not in info.data['stops_df'].columns:
            raise ValueError(f'{v} is not a column in the dataframe')
        return v

    # Don't need the following. Pydantic will make sure it's convertible to a date or datetime which we know
    # can be converted to a pd.Timestamp. We just need to convert it ourselves.
    # @field_validator('start_analysis_dt', 'end_analysis_dt')
    # def convertible_to_pd_timestamp(cls, v: date | datetime | pd.Timestamp, info: FieldValidationInfo):
    #     try:
    #         start_analysis_dt_ts = pd.Timestamp(v)
    #     except ValueError as error:
    #         raise ValueError(f'Cannot convert {v} to Timestamp\n{error}')
    # End date >= start date
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

    # def __str__(self):
    #     """Pretty string representation of scenario parameters"""
    #     # TODO - write str method for Scenario class
    #     return str(self)

    # This is v1 pydantic which is now deprecated in favor of ConfigDict (see before field declarations)
    # class Config:
    #     arbitrary_types_allowed = True


class Scenario:
    """User facing class to gather inputs for a hillmaker scenario"""

    def __init__(
            self,
            params_dict: Optional[Dict] = None,
            params_path: Optional[str | Path] = None,
            **kwargs
    ):
        # Create empty dict for input parameters
        params = {}

        # If params_dict is not None, merge into params
        if params_dict is not None:
            params.update(params_dict)

        # If params_path is not None, merge into params
        if params_path is not None:
            with open(params_path, "rb") as f:
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

        params_model = Parameters(**params)
        self.params = params_model
        self.hills = {}

    # For now, the only method is make_hills which simply passes on the parameters model
    # to the module level make_hills function. This should make it easy to also call make_hills directly.
    def make_hills(self):
        self.hills = make_hills(self.params)

    def get_plot(self, flow_metric: str = 'occupancy', day_of_week: str = 'week'):
        """
        Get plot object for specified flow metric and whether full week or specified day of week.

        Parameters
        ----------
        flow_metric : str
            Either of 'arrivals', 'departures', 'occupancy' ('a', 'd', and 'o' are sufficient).
            Default='occupancy'
        day_of_week : str
            Either of 'week', 'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'. Default='week'

        Returns
        -------
        plot object from matplotlib

        """
        flow_metrics = {'a': 'arrivals', 'd': 'departures', 'o': 'occupancy'}
        flow_metric_str = flow_metrics[flow_metric[0].lower()]
        if day_of_week.lower() != 'week':
            day_of_week_str = day_of_week[:3].lower()
        else:
            day_of_week_str = 'week'

        plot_name = f'{self.params.scenario_name}_{flow_metric_str}_plot_{day_of_week_str}'
        try:
            plot = self.hills['plots'][plot_name]
            return plot
        except KeyError as error:
            print(f'The plot {error} does not exist.')
            return None

    def prep_scenario(self) :
        """
        Do additional validation checking, pd.Timestamp -> np.datetime64 conversions and filtering stop data.

        Parameters
        ----------


        Returns
        -------
        Updated Scenario object

        """

        try:
            start_analysis_dt_ts = pd.Timestamp(self.params.start_analysis_dt)
        except ValueError as error:
            raise ValueError(f'Cannot convert {self.params.start_analysis_dt} to Timestamp\n{error}')

        try:
            end_analysis_dt_ts = pd.Timestamp(self.params.end_analysis_dt).floor("d") + pd.Timedelta(86399, "s")
        except ValueError as error:
            raise ValueError(f'Cannot convert {self.params.end_analysis_dt} to Timestamp\n{error}')

        # numpy datetime64 versions of analysis span end points
        # start_analysis_dt_np = start_analysis_dt_ts.to_datetime64()
        self.params.start_analysis_dt = start_analysis_dt_ts.to_datetime64()
        # end_analysis_dt_np = end_analysis_dt_ts.to_datetime64()
        self.params.end_analysis_dt = end_analysis_dt_ts.to_datetime64()

        # Looking for missing entry and departure timestamps
        num_recs_missing_entry_ts = self.stops_df[self.in_field].isna().sum()
        num_recs_missing_exit_ts = self.stops_df[self.out_field].isna().sum()
        if num_recs_missing_entry_ts > 0:
            logger.warning(f'{num_recs_missing_entry_ts} records with missing entry timestamps - records ignored')

        # Update departure timestamp for missing values if no_censored_departures=False
        if not self.adjust_censored_departures:
            # num_recs_uncensored = num_recs_missing_exit_ts
            if num_recs_missing_exit_ts > 0:
                msg = 'records with missing exit timestamps - end of analysis range used for occupancy purposes'
                logger.info(
                    f'{num_recs_missing_exit_ts} {msg}')
                uncensored_out_field = f'{self.out_field}_uncensored'
                uncensored_out_value = pd.Timestamp(self.end_analysis_dt).floor("d") + pd.Timedelta(1, "d")
                self.stops_df[uncensored_out_field] = self.stops_df[self.out_field].fillna(
                    value=uncensored_out_value)
                active_out_field = uncensored_out_field
            else:
                # Records with missing departures will be ignored
                active_out_field = self.out_field
                if num_recs_missing_exit_ts > 0:
                    logger.warning(
                        f'{num_recs_missing_exit_ts} records with missing exit timestamps - records ignored')
        else:
            active_out_field = self.out_field

        # Filter out records that don't overlap the analysis span or have missing entry timestamps
        self.stops_df = self.stops_df.loc[(self.stops_df[self.in_field] < end_analysis_dt_ts) &
                                          (~self.stops_df[self.in_field].isna()) &
                                          (self.stops_df[active_out_field] >= start_analysis_dt_ts)]

        # reset index of df to ensure sequential numbering
        self.stops_df = self.stops_df.reset_index(drop=True)

        return 0

    def __str__(self):
        """Pretty string representation of a scenario"""
        # TODO - write str method for Scenario class
        return str(self.params.dict())
