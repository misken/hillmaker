from datetime import datetime, date
from pathlib import Path
import logging
from typing import List, Tuple, Dict
from enum import IntEnum

import pandas as pd
import numpy as np
from pydantic import BaseModel, field_validator, model_validator, confloat, FieldValidationInfo, ConfigDict

# import hillmaker as hm
from hillmaker.hills import compute_hills_stats, _make_hills, get_plot, get_summary_df, get_bydatetime_df
from hillmaker.plotting import make_week_hill_plot, make_daily_hill_plot

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
    cap : int, optional
        Capacity of area being analyzed, default is None. Used only to add capacity line to occupancy plots.
    nonstationary_stats : bool, optional
       If True, datetime bin stats are computed. Else, they aren't computed. Default is True
    stationary_stats : bool, optional
       If True, overall, non-time bin dependent, stats are computed. Else, they aren't computed. Default is True
    export_bydatetime_csv : bool, optional
       If True, bydatetime DataFrames are exported to csv files. Default is False.
    export_summaries_csv : bool, optional
       If True, summary DataFrames are exported to csv files. Default is False.
    make_all_dow_plots : bool, optional
       If True, day of week plots are created for occupancy, arrival, and departure. Default is True.
    make_all_week_plots : bool, optional
       If True, full week plots are created for occupancy, arrival, and departure. Default is True.
    export_all_dow_plots : bool, optional
       If True, day of week plots are exported for occupancy, arrival, and departure. Default is False.
    export_all_week_plots : bool, optional
       If True, full week plots are exported for occupancy, arrival, and departure. Default is False.
    xlabel : str
        x-axis label, default='Hour'
    ylabel : str
        y-axis label, default='Occupancy'
    output_path : str or Path, optional
        Destination path for exported csv and png files, default is current directory
    verbosity : int, optional
        Used to set level in loggers. 0=logging.WARNING (default=0), 1=logging.INFO, 2=logging.DEBUG
    los_units : str, optional
        The time units for length of stay analysis.
        See https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.html for allowable values (smallest
        value allowed is 'seconds', largest is 'days'. The default
        is 'hours'.

    Attributes
    ----------
    stops_preprocessed_df : DataFrame (initialized to None)
        Preprocessed dataframe that only contains necessary fields and does not include records with missing
            timestamps for the entry and/or exit time. This `DataFrame` is the one used for hill making.

    hills : dict (initialized to None)
        Stores results of `make_hills`.


    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')

    # Required parameters
    scenario_name: str
    stops_df: pd.DataFrame
    in_field: str
    out_field: str
    # TODO - what if a pandas Timestamp or numpy datetime64 is passed in?
    # See https://github.com/pydantic/pydantic/discussions/6972
    start_analysis_dt: date | datetime | pd.Timestamp | np.datetime64
    end_analysis_dt: date | datetime | pd.Timestamp | np.datetime64
    # Optional parameters
    # stop_data_csv: str | Path | None = None
    cat_field: str | None = None
    bin_size_minutes: int = 60
    cats_to_exclude: List[str] | None = None
    occ_weight_field: str | None = None
    percentiles: Tuple[confloat(ge=0.0, le=1.0)] | List[confloat(ge=0.0, le=1.0)] = (0.25, 0.5, 0.75, 0.95, 0.99)
    nonstationary_stats: bool = True
    stationary_stats: bool = True
    edge_bins: EdgeBinsEnum = EdgeBinsEnum.FRACTIONAL
    output_path: str | Path = Path('.')
    export_bydatetime_csv: bool = False
    export_summaries_csv: bool = False
    make_all_dow_plots: bool = False
    make_all_week_plots: bool = False
    export_all_dow_plots: bool = False
    export_all_week_plots: bool = False
    cap: int | None = None
    xlabel: str | None = 'Hour'
    ylabel: str | None = 'Patients'
    verbosity: int = VerbosityEnum.WARNING
    los_units: str = 'hours'
    # Attributes
    stops_preprocessed_df: pd.DataFrame | None = None
    los_field_name: str | None = None
    hills: dict | None = None

    # Ensure required fields and submitted optional fields exist
    @field_validator('in_field', 'out_field', 'cat_field', 'occ_weight_field')
    def field_exists(cls, v: str, info: FieldValidationInfo):
        if v is not None and v not in info.data['stops_df'].columns:
            raise ValueError(f'{v} is not a column in the dataframe')
        return v

    @field_validator('start_analysis_dt', 'end_analysis_dt')
    def validate_start_end_date(cls, v: date | datetime, info: FieldValidationInfo):
        """
        Ensure start and end dates for analysis are convertible to numpy datetime64 and do the conversion.

        Parameters
        ----------
        v
        info

        Returns
        -------

        """

        try:
            analysis_dt_ts = pd.Timestamp(v)
            analysis_dt_np = analysis_dt_ts.to_datetime64()
            return analysis_dt_np
        except ValueError as error:
            raise ValueError(f'Cannot convert {v} to to a numpy datetime64 object.\n{error}')

    @field_validator('bin_size_minutes')
    def bin_size_minutes_divides(cls, v: int):
        """
        Ensure bin_size_minutes divides into 1440 with no remainder

        Parameters
        ----------
        v : int

        Returns
        -------
        int
        """
        if 1440 % v > 0:
            raise ValueError('bin_size_minutes must divide into 1440 with no remainder')
        return v

    @field_validator('bin_size_minutes')
    def los_units_strings(cls, v: str):
        """
        Ensure los_units is a valid time unit string

        Parameters
        ----------
        v : str

        Returns
        -------
        str
        """
        allowable = ['days', 'day',
                     'hours', 'hour', 'hr', 'h',
                     'minutes', 'minute', 'min', 'm',
                     'seconds', 'second', 'sec']
        if v not in allowable:
            raise ValueError(f'{v} is not a valid time unit code. Must be one of {allowable}')
        return v

    @model_validator(mode='after')
    def date_relationship(self) -> 'Scenario':
        """
        Start date for analysis must be before end date.

        Returns
        -------
        Scenario

        """
        if self.end_analysis_dt <= self.start_analysis_dt:
            raise ValueError(f'end date must be > start date')
        return self

    @model_validator(mode='after')
    def preprocess_stops_df(self) -> 'Scenario':
        """
        Create preprocessed dataframe that only contains necessary fields and does not include records with missing
        timestamps for the entry and/or exit time.

        Returns
        -------
        Scenario - `stops_preprocessed_df` is populated

        """

        # Count missing timestamps
        num_recs_missing_entry_ts = self.stops_df[self.in_field].isna().sum()
        num_recs_missing_exit_ts = self.stops_df[self.out_field].isna().sum()
        if num_recs_missing_entry_ts > 0:
            logger.warning(f'{num_recs_missing_entry_ts} records with missing entry timestamps - records ignored')
        if num_recs_missing_exit_ts > 0:
            logger.warning(f'{num_recs_missing_exit_ts} records with missing exit timestamps - records ignored')

        # Create mutable copy of stops_df containing only necessary fields
        stops_preprocessed_df = pd.DataFrame(
            {self.in_field: self.stops_df[self.in_field], self.out_field: self.stops_df[self.out_field]})
        if self.cat_field is not None:
            stops_preprocessed_df[self.cat_field] = self.stops_df[self.cat_field]

        # Filter out records that don't overlap the analysis span or have missing entry and/or exit timestamps
        stops_preprocessed_df = \
            stops_preprocessed_df.loc[(stops_preprocessed_df[self.in_field] < self.end_analysis_dt) &
                                      (~stops_preprocessed_df[self.in_field].isna()) &
                                      (~stops_preprocessed_df[self.out_field].isna()) &
                                      (stops_preprocessed_df[self.out_field] >= self.start_analysis_dt)]

        # Compute additional fields used for analysis
        los_field_name = f'los_{self.los_units}'
        stops_preprocessed_df[los_field_name] = (stops_preprocessed_df[self.out_field] -
                                                 stops_preprocessed_df[self.in_field]) / pd.Timedelta(1, self.los_units)

        # reset index of df to ensure sequential numbering
        stops_preprocessed_df = stops_preprocessed_df.reset_index(drop=True)
        self.stops_preprocessed_df = stops_preprocessed_df
        self.los_field_name = los_field_name

        return self

    def compute_hills_stats(self):
        """
        Computes the bydatetime and summary statistics (no plotting or exporting).

        Returns
        -------
        dict stored in `hills` attribute of Scenario object

        """

        hills = compute_hills_stats(self)
        self.hills = hills

    def make_hills(self):
        """
        Wrapper for module level `hillmaker.make_hills()` function.

        Returns
        -------
        dict stored in `hills` attribute of Scenario object

        """
        # Get dict version of pydantic model
        # inputs_dict = self.model_dump()
        # # Remove output related attributes
        # non_input_attributes = ['hills', 'stops_preprocessed_df']
        # for att in non_input_attributes:
        #     inputs_dict.pop(att, None)
        #
        # # Pass remaining parameters to hillmaker.make_hills()

        self.hills = _make_hills(self)
        # return self

    def make_weekly_plot(self, metric: str = 'occupancy',
                         cap: int = None,
                         plot_style: str = 'ggplot',
                         figsize: tuple = (15, 10),
                         bar_color_mean: str = 'steelblue',
                         percentiles: Tuple[float] | List[float] = (0.95, 0.75),
                         pctile_color: Tuple[str] | List[str] = ('black', 'grey'),
                         pctile_linestyle: Tuple[str] | List[str] = ('-', '--'),
                         pctile_linewidth: Tuple[float] | List[float] = (0.75, 0.75),
                         cap_color: str = 'r',
                         xlabel: str = '',
                         ylabel: str = '',
                         suptitle: str = '',
                         suptitle_properties: None | Dict = None,
                         title: str = '',
                         title_properties: None | Dict = None,
                         legend_properties: None | Dict = None,
                         first_dow: str = 'mon',
                         export_path: Path | str | None = None, ):

        bin_size_minutes = self.bin_size_minutes
        scenario_name = self.scenario_name

        metric_code = metric.lower()[0]
        summary_df = self.get_summary_df(metric_code, by_category=False, stationary=False)

        plot = make_week_hill_plot(summary_df=summary_df, metric=metric,
                                   bin_size_minutes=bin_size_minutes,
                                   cap=cap,
                                   cap_color=cap_color,
                                   plot_style=plot_style,
                                   figsize=figsize,
                                   bar_color_mean=bar_color_mean,
                                   percentiles=percentiles,
                                   pctile_color=pctile_color,
                                   pctile_linestyle=pctile_linestyle,
                                   pctile_linewidth=pctile_linewidth,
                                   suptitle=suptitle,
                                   suptitle_properties=suptitle_properties,
                                   title=title,
                                   title_properties=title_properties,
                                   legend_properties=legend_properties,
                                   xlabel=xlabel,
                                   ylabel=ylabel,
                                   first_dow=first_dow,
                                   scenario_name=scenario_name,
                                   export_path=export_path)

        return plot

    def make_daily_plot(self, day_of_week: str, metric: str = 'occupancy',
                        cap: int = None,
                        plot_style: str = 'ggplot',
                        figsize: tuple = (15, 10),
                        bar_color_mean: str = 'steelblue',
                        percentiles: Tuple[float] | List[float] = (0.95, 0.75),
                        pctile_color: Tuple[str] | List[str] = ('black', 'grey'),
                        pctile_linestyle: Tuple[str] | List[str] = ('-', '--'),
                        pctile_linewidth: Tuple[float] | List[float] = (0.75, 0.75),
                        cap_color: str = 'r',
                        xlabel: str = '',
                        ylabel: str = '',
                        suptitle: str = '',
                        suptitle_properties: None | Dict = None,
                        title: str = '',
                        title_properties: None | Dict = None,
                        legend_properties: None | Dict = None,
                        export_path: Path | str | None = None, ):

        bin_size_minutes = self.bin_size_minutes
        scenario_name = self.scenario_name

        metric_code = metric.lower()[0]
        summary_df = self.get_summary_df(metric_code, by_category=False, stationary=False)

        plot = make_daily_hill_plot(summary_df=summary_df, day_of_week=day_of_week, metric=metric,
                                    bin_size_minutes=bin_size_minutes,
                                    cap=cap,
                                    cap_color=cap_color,
                                    plot_style=plot_style,
                                    figsize=figsize,
                                    bar_color_mean=bar_color_mean,
                                    percentiles=percentiles,
                                    pctile_color=pctile_color,
                                    pctile_linestyle=pctile_linestyle,
                                    pctile_linewidth=pctile_linewidth,
                                    suptitle=suptitle,
                                    suptitle_properties=suptitle_properties,
                                    title=title,
                                    title_properties=title_properties,
                                    legend_properties=legend_properties,
                                    xlabel=xlabel,
                                    ylabel=ylabel,
                                    scenario_name=scenario_name,
                                    export_path=export_path)

        return plot

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

        plot = get_plot(self.hills, flow_metric, day_of_week)
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
        df = get_summary_df(self.hills, flow_metric=flow_metric, by_category=by_category, stationary=stationary)
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
        df = get_bydatetime_df(self.hills, by_category=by_category)
        return df

    def __str__(self):
        """Pretty string representation of a scenario"""
        # TODO - write str method for Scenario class
        return str(self.model_dump())
