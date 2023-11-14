"""
The :mod:`hillmaker.scenario` module defines the `Scenario` class and the OO API for using hillmaker.
"""

# Copyright 2022-2023 Mark Isken, Jacob Norman

from datetime import datetime, date
from pathlib import Path
import logging
from typing import List, Tuple, Dict, Optional
from enum import IntEnum
from argparse import Namespace

import pandas as pd
import numpy as np
from pydantic import BaseModel, field_validator, model_validator, confloat, ConfigDict

# import hillmaker as hm
from hillmaker.hills import compute_hills_stats, _make_hills, get_plot, get_summary_df, get_bydatetime_df
from hillmaker.hills import get_los_plot, get_los_stats
from hillmaker.plotting import make_week_hill_plot, make_daily_hill_plot
from hillmaker.summarize import compute_implied_operating_hours

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
    data : str, Path, or DataFrame
        Base data containing one row per visit. If Path-like, data is read into a DataFrame.
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
        Number of minutes in each time bin of the day, default is 60. This bin size is used for plots and reporting and
        is an aggregation of computations done at the finer bin size resolution specified by `resolution_bin_size_mins`.
        Use a value that divides into 1440 with no remainder.
    cats_to_exclude : list, optional
        Category values to ignore, default is None
    occ_weight_field : str, optional
        Column name corresponding to the weights to use for occupancy incrementing, default is None
        which corresponds to a weight of 1.0
    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)
    los_units : str, optional
        The time units for length of stay analysis.
        See https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.html for allowable values (smallest
        value allowed is 'seconds', largest is 'days'. The default is 'hours'.

    export_bydatetime_csv : bool, optional
       If True, bydatetime DataFrames are exported to csv files. Default is False.
    export_summaries_csv : bool, optional
       If True, summary DataFrames are exported to csv files. Default is False.
    csv_export_path : str or Path, optional
        Destination path for exported csv and png files, default is current directory

    make_all_dow_plots : bool, optional
       If True, day of week plots are created for occupancy, arrivals, and departures. Default is False.
    make_all_week_plots : bool, optional
       If True, full week plots are created for occupancy, arrivals, and departures. Default is True.
    export_all_dow_plots : bool, optional
       If True, day of week plots are exported for occupancy, arrivals, and departures. Default is False.
    export_all_week_plots : bool, optional
       If True, full week plots are exported for occupancy, arrivals, and departures. Default is False.
    plot_export_path : str or None, default is None
        If not None, plot is exported to `export_path`

    plot_style : str, optional
        Matplotlib built in style name. Default is 'ggplot'.
    figsize : Tuple, optional
        Figure size. Default is (15, 10)
    bar_color_mean : str, optional
        Matplotlib color name for the bars representing mean values. Default is 'steelblue'
    alpha : float, optional
        Transparency level for bars. Default = 0.5.
    plot_percentiles : list or tuple of floats (e.g. [0.75, 0.95]), optional
        Which percentiles to plot. Default is (0.95, 0.75)
    pctile_color : list or tuple of color codes (e.g. ['blue', 'green'] or list('gb'), optional
        Line color for each percentile series plotted. Order should match order of percentiles list.
        Default is ('black', 'grey').
    pctile_linestyle : List or tuple of line styles (e.g. ['-', '--']), optional
        Line style for each percentile series plotted. Default is ('-', '--').
    pctile_linewidth : List or tuple of line widths in points (e.g. [1.0, 0.75])
        Line width for each percentile series plotted. Default is (0.75, 0.75).
    cap : int, optional
        Capacity of area being analyzed, default is None
    cap_color : str, optional
        matplotlib color code, default='r'
    xlabel : str, optional
        x-axis label, default='Hour'
    ylabel : str, optional
        y-axis label, default='Patients'
    main_title : str, optional
        Main title for plot, default = 'Occupancy by time of day and day of week - {scenario_name}'
    main_title_properties : None or dict, optional
        Dict of `suptitle` properties, default={{'loc': 'left', 'fontsize': 16}}
    subtitle : str, optional
        title for plot, default = 'All categories'
    subtitle_properties : None or dict, optional
        Dict of `title` properties, default={{'loc': 'left', 'style': 'italic'}}
    legend_properties : None or dict, optional
        Dict of `legend` properties, default={{'loc': 'best', 'frameon': True, 'facecolor': 'w'}}
    first_dow : str, optional
        Controls which day of week appears first in plot. One of 'mon', 'tue', 'wed', 'thu', 'fri', 'sat, 'sun'

    edge_bins: int, default 1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=entire bin
    highres_bin_size_minutes : int, optional
        Number of minutes in each time bin of the day used for initial computation of the number of arrivals,
        departures, and the occupancy level. This value should be <= `bin_size_minutes`. The shorter the duration of
        stays, the smaller the resolution should be. The current default is 5 minutes.
    keep_highres_bydatetime : bool, optional
        Save the high resolution bydatetime dataframe in hills attribute. Default is False.
    nonstationary_stats : bool, optional
       If True, datetime bin stats are computed. Else, they aren't computed. Default is True
    stationary_stats : bool, optional
       If True, overall, non-time bin dependent, stats are computed. Else, they aren't computed. Default is True
    verbosity : int, optional
        Used to set level in loggers. 0=logging.WARNING (default=0), 1=logging.INFO, 2=logging.DEBUG


    Attributes
    ----------
    stops_preprocessed_df : DataFrame (initialized to None)
        Preprocessed dataframe that only contains necessary fields and does not include records with missing
            timestamps for the entry and/or exit time. This `DataFrame` is the one used for hill making.

    hills : dict (initialized to None)
        Stores results of `make_hills`.

    Examples
    --------
    Example 1 - using keyword arguments::

        # Required inputs
        scenario_name = 'ssu_oo_1'
        stops_df = ssu_stops_df
        in_field_name = 'InRoomTS'
        out_field_name = 'OutRoomTS'
        start_date = '2024-06-01'
        end_date = pd.Timestamp('8/31/2024')

        # Optional inputs
        cat_field_name = 'PatType'
        bin_size_minutes = 60

        scenario_1 = hm.Scenario(scenario_name=scenario_name,
                             data=stops_df,
                             in_field=in_field_name,
                             out_field=out_field_name,
                             start_analysis_dt=start_date,
                             end_analysis_dt=end_date,
                             cat_field=cat_field_name,
                             bin_size_minutes=bin_size_minutes)

    Example 2 - using TOML config file

    Here's what an example config file might look like.::

        [scenario_data]
        scenario_name = "ss_oo_2"
        data = "./data/ssu_2024.csv"

        [fields]
        in_field = "InRoomTS"
        out_field = "OutRoomTS"
        # Just remove the following line if no category field
        cat_field = "PatType"

        [analysis_dates]
        start_analysis_dt = 2024-01-02
        end_analysis_dt = 2024-03-30

        [settings]
        bin_size_minutes = 120
        verbosity = 1
        csv_export_path = './output'
        plot_export_path = './output'

        # Add any additional arguments here
        # Strings should be surrounded in double quotes
        # Floats and ints are specified in the normal way as values
        # Dates are specified as shown above

        # For arguments that take lists, the entries look
        # just like Python lists and following the other rules above

        # cats_to_exclude = ["IVT", "OTH"]
        # percentiles = [0.5, 0.8, 0.9]

        # For arguments that take dictionaries, do this:
        # main_title_properties = {loc = 'left', fontsize = 16}
        # subtitle_properties = {loc = 'left', style = 'italic'}
        # legend_properties = {loc = 'best', frameon = true, facecolor = 'w'}

    Then we can pass the filename like this::

        scenario_2 = hm.create_scenario(config_path='./input/ssu_oo_2.toml')

    Example 3 - using a dictionary of input values::

        ssu_oo_3_dict = {
        'scenario_name': 'ssu_oo_3',
        'data': ssu_stops_df,
        'in_field': 'InRoomTS',
        'out_field': 'OutRoomTS',
        'start_analysis_dt': '2024-01-01',
        'end_analysis_dt': '2024-09-30',
        'cat_field': 'PatType',
        'bin_size_minutes': 60
        }

        ssu_oo_3 = hm.create_scenario(params_dict=ssu_oo_3_dict)
        print(ssu_oo_3)


    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')

    # Required parameters
    scenario_name: str
    data: str | Path | pd.DataFrame
    in_field: str
    out_field: str
    start_analysis_dt: date | datetime | pd.Timestamp | np.datetime64
    end_analysis_dt: date | datetime | pd.Timestamp | np.datetime64
    # Optional parameters
    # config: Path | str | None = None
    cat_field: str | None = None
    bin_size_minutes: int = 60
    cats_to_exclude: List[str] | None = None
    occ_weight_field: str | None = None
    percentiles: Tuple[confloat(ge=0.0, le=1.0)] | List[confloat(ge=0.0, le=1.0)] = (0.25, 0.5, 0.75, 0.95, 0.99)
    los_units: str | None = 'hours'

    export_bydatetime_csv: bool = False
    export_summaries_csv: bool = False
    csv_export_path: Path | str | None = Path('.')

    make_all_dow_plots: bool = False
    make_all_week_plots: bool = True
    export_all_dow_plots: bool = False
    export_all_week_plots: bool = False
    plot_export_path: Path | str | None = None

    # Plot options
    plot_style: str | None = 'ggplot'
    figsize: tuple = (15, 10)
    bar_color_mean: str | None = 'steelblue'
    alpha: float = 0.5
    plot_percentiles: Tuple[float] | List[float] = (0.95, 0.75)
    pctile_color: Tuple[str] | List[str] = ('black', 'grey')
    pctile_linestyle: Tuple[str] | List[str] = ('-', '--')
    pctile_linewidth: Tuple[float] | List[float] = (0.75, 0.75)
    cap: int | None = None
    cap_color: str | None = 'r'
    xlabel: str | None = 'Hour'
    ylabel: str | None = 'Volume'
    main_title: str | None = ''
    main_title_properties: None | Dict = {'loc': 'left', 'fontsize': 16}
    subtitle: str | None = ''
    subtitle_properties: None | Dict = {'loc': 'left', 'style': 'italic'}
    legend_properties: None | Dict = {'loc': 'best', 'frameon': True, 'facecolor': 'w'}
    first_dow: str = 'mon'

    # Advanced parameters
    edge_bins: EdgeBinsEnum = EdgeBinsEnum.FRACTIONAL
    highres_bin_size_minutes: int = 5
    keep_highres_bydatetime: bool = False
    nonstationary_stats: bool = True
    stationary_stats: bool = True
    verbosity: int = VerbosityEnum.WARNING
    # Attributes
    stops_preprocessed_df: pd.DataFrame | None = None
    los_field_name: str | None = None
    hills: dict | None = None

    @field_validator('start_analysis_dt')
    def _validate_start_date(cls, v: date | datetime):
        """
        Ensure start date for analysis is convertible to numpy datetime64 and do the conversion.

        Parameters
        ----------
        v : date | datetime

        Returns
        -------
        datetime64

        """

        try:
            start_analysis_dt_ts = pd.Timestamp(v)
            start_analysis_dt_np = start_analysis_dt_ts.to_datetime64()
            return start_analysis_dt_np
        except ValueError as error:
            raise ValueError(f'Cannot convert {v} to to a numpy datetime64 object.\n{error}')

    @field_validator('end_analysis_dt')
    def _validate_end_date(cls, v: date | datetime):
        """
        Ensure end date for analysis is convertible to numpy datetime64 and do the conversion.
        Adjust end date to include entire day.

        Parameters
        ----------
        v : date | datetime

        Returns
        -------
        datetime64

        """

        try:
            end_analysis_dt_ts = pd.Timestamp(v).floor("d") + pd.Timedelta(86399, "s")
            end_analysis_dt_np = end_analysis_dt_ts.to_datetime64()
            return end_analysis_dt_np
        except ValueError as error:
            raise ValueError(f'Cannot convert {v} to to a numpy datetime64 object.\n{error}')

    @field_validator('bin_size_minutes')
    def _bin_size_minutes_divides(cls, v: int):
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

    @field_validator('los_units')
    def _los_units_strings(cls, v: str):
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
    def _stop_data(self) -> 'Scenario':
        """If data is a DataFrame return it, else read the csv file into a DataFrame and return that."""
        if isinstance(self.data, pd.DataFrame):
            return self
        else:
            stops_df = pd.read_csv(self.data, parse_dates=[self.in_field, self.out_field])
            self.data = stops_df
            return self

    @model_validator(mode='after')
    def _fields_exist(self) -> 'Scenario':
        """Make sure fields exist """

        fields_to_check = [self.in_field, self.out_field, self.cat_field, self.occ_weight_field]
        for field in fields_to_check:
            if field is not None and field not in self.data.columns:
                raise ValueError(f'{field} is not a column in the dataframe')

        return self

    @model_validator(mode='after')
    def _date_relationships(self) -> 'Scenario':
        """
        Start date for analysis must be before end date and on or after earliest arrival.

        Returns
        -------
        Scenario

        """
        if self.end_analysis_dt <= self.start_analysis_dt:
            raise ValueError(f'end date must be > start date')

        min_intime = self.data[self.in_field].min()
        max_outtime = self.data[self.out_field].max()

        if max_outtime < self.start_analysis_dt:
            raise ValueError(
                f'latest departure time of {max_outtime} is prior to start analysis date of {self.start_analysis_dt}')

        if min_intime > self.end_analysis_dt:
            raise ValueError(
                f'earliest arrival time of {min_intime} is after end analysis date of {self.end_analysis_dt}')

        if (min_intime - self.start_analysis_dt) > pd.Timedelta(48, 'h'):
            raise ValueError(
                f'start analysis date {self.start_analysis_dt} is > 48 hours before earliest arrival of {min_intime}')
        
        if (self.end_analysis_dt - max_outtime) > pd.Timedelta(48, 'h'):
            raise ValueError(
                f'end analysis date {self.end_analysis_dt} is > 48 hours before latest departure of {max_outtime}')

        return self

    @model_validator(mode='after')
    def _bin_size_relationships(self) -> 'Scenario':

        if self.bin_size_minutes < self.highres_bin_size_minutes:
            raise ValueError(
                f'highres_bin_size_minutes ({self.highres_bin_size_minutes}) must be <= bin_size_minutes ({self.bin_size_minutes})')

        if self.edge_bins == EdgeBinsEnum.FRACTIONAL and not self.keep_highres_bydatetime:
            # No need to compute bydatetime at high resolution
            self.highres_bin_size_minutes = self.bin_size_minutes

        return self

    @model_validator(mode='after')
    def _preprocess_stops_df(self) -> 'Scenario':
        """
        Create preprocessed dataframe that only contains necessary fields and does not include records with missing
        timestamps for the entry and/or exit time.

        Returns
        -------
        Scenario - `stops_preprocessed_df` is populated

        """

        # Count missing timestamps
        num_recs_missing_entry_ts = self.data[self.in_field].isna().sum()
        num_recs_missing_exit_ts = self.data[self.out_field].isna().sum()
        if num_recs_missing_entry_ts > 0:
            logger.warning(f'{num_recs_missing_entry_ts} records with missing entry timestamps - records ignored')
        if num_recs_missing_exit_ts > 0:
            logger.warning(f'{num_recs_missing_exit_ts} records with missing exit timestamps - records ignored')

        # Create mutable copy of stops_df containing only necessary fields
        stops_preprocessed_df = pd.DataFrame(
            {self.in_field: self.data[self.in_field], self.out_field: self.data[self.out_field]})
        if self.cat_field is not None:
            stops_preprocessed_df[self.cat_field] = self.data[self.cat_field]

        # Filter out records that don't overlap the analysis span or have missing entry and/or exit timestamps
        stops_preprocessed_df = \
            stops_preprocessed_df.loc[(stops_preprocessed_df[self.in_field] < self.end_analysis_dt) &
                                      (~stops_preprocessed_df[self.in_field].isna()) &
                                      (~stops_preprocessed_df[self.out_field].isna()) &
                                      (stops_preprocessed_df[self.out_field] > self.start_analysis_dt)]

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

        self.hills = _make_hills(self)
        # return self

    def make_weekly_plot(self, metric: str = 'occupancy', **kwargs):
        """
        Create weekly plot

        Parameters
        ----------
        metric : str
            Some abbreviated version of occupancy, arrivals or departures
        kwargs : dict
            Plot related keyword arguments

        Returns
        -------
        matplotlib.Figure

        Example
        -------
        scenario_1.make_weekly_plot(metric='occupancy', plot_export_path='./output', cap=40, plot_style='default')

        """

        params_dict = vars(self).copy()
        params_dict.update(kwargs)
        params = Namespace(**params_dict)

        metric_code = metric.lower()[0]
        summary_df = self.get_summary_df(metric_code, by_category=False, stationary=False)

        plot = make_week_hill_plot(summary_df=summary_df, metric=metric,
                                   bin_size_minutes=params.bin_size_minutes,
                                   cap=params.cap,
                                   cap_color=params.cap_color,
                                   plot_style=params.plot_style,
                                   figsize=params.figsize,
                                   bar_color_mean=params.bar_color_mean,
                                   alpha=params.alpha,
                                   plot_percentiles=params.plot_percentiles,
                                   pctile_color=params.pctile_color,
                                   pctile_linestyle=params.pctile_linestyle,
                                   pctile_linewidth=params.pctile_linewidth,
                                   main_title=params.main_title,
                                   main_title_properties=params.main_title_properties,
                                   subtitle=params.subtitle,
                                   subtitle_properties=params.subtitle_properties,
                                   legend_properties=params.legend_properties,
                                   xlabel=params.xlabel,
                                   ylabel=params.ylabel,
                                   first_dow=params.first_dow,
                                   scenario_name=params.scenario_name,
                                   plot_export_path=params.plot_export_path)

        return plot

    def make_daily_plot(self, day_of_week: str, metric: str = 'occupancy', **kwargs):
        """
        Create daily plot

        Parameters
        ----------
        day_of_week : str
            One of 'mon', 'tue', 'wed', 'thu', 'fri', 'sat, 'sun'
        metric : str
            One of 'occupancy', 'arrivals', 'departures'
        kwargs : dict
            Plot related keyword arguments

        Returns
        -------
        matplotlib.Figure

        Example
        -------
        scenario_1.make_daily_plot(day_of_week = 'mon', metric='arrivals',
                                    plot_export_path='./output', plot_style='default')

        """

        params_dict = vars(self).copy()
        params_dict.update(kwargs)
        params = Namespace(**params_dict)

        metric_code = metric.lower()[0]
        summary_df = self.get_summary_df(metric_code, by_category=False, stationary=False)

        plot = make_daily_hill_plot(summary_df=summary_df, day_of_week=day_of_week, metric=metric,
                                    bin_size_minutes=params.bin_size_minutes,
                                    cap=params.cap,
                                    cap_color=params.cap_color,
                                    plot_style=params.plot_style,
                                    figsize=params.figsize,
                                    bar_color_mean=params.bar_color_mean,
                                    alpha=params.alpha,
                                    plot_percentiles=params.plot_percentiles,
                                    pctile_color=params.pctile_color,
                                    pctile_linestyle=params.pctile_linestyle,
                                    pctile_linewidth=params.pctile_linewidth,
                                    main_title=params.main_title,
                                    main_title_properties=params.main_title_properties,
                                    subtitle=params.subtitle,
                                    subtitle_properties=params.subtitle_properties,
                                    legend_properties=params.legend_properties,
                                    xlabel=params.xlabel,
                                    ylabel=params.ylabel,
                                    scenario_name=params.scenario_name,
                                    plot_export_path=params.plot_export_path)

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

    def get_los_plot(self, by_category: bool = True):
        """
        Get length of stay histogram from length of stay summary

        Parameters
        ----------
        by_category : bool
            Default=True corresponds to category specific statistics. A value of False gives overall statistics.

        Returns
        -------
        Matplotlib plot

        """
        plot = get_los_plot(self.hills, by_category=by_category)
        return plot

    def get_los_stats(self, by_category: bool = True):
        """
        Get length of stay stats table from length of stay summary

        Parameters
        ----------
        by_category : bool
            Default=True corresponds to category specific statistics. A value of False gives overall statistics.

        Returns
        -------
        pandas Styler

        """
        stats = get_los_stats(self.hills, by_category=by_category)
        return stats

    def compute_implied_operating_hours(self, by_category: bool = True,
                                        statistic: str = 'mean', threshold: float = 0.2):
        """
        Infers operating hours of underlying data.

        Computes implied operating hours based on exceeding a percentage of the
        maximum occupancy for a given statistic.

        Parameters
        ----------
        by_category : bool
            Default=True corresponds to category specific statistics. A value of False gives overall statistics.

        statistic : str
            Column name for the statistic value. Default is 'mean'.

        threshold : float
            Percentage of maximum occupancy that will be considered 'open' for
            operating purposes, inclusive. Default is 0.2.

        Returns
        -------
        pandas styler object

        """
        occ_df = get_summary_df(self.hills, by_category=by_category)

        # get cat_field name from Scenario if specified
        if by_category:
            cat = self.model_dump()['cat_field']
        else:
            cat = None

        styler = compute_implied_operating_hours(occ_df, cat_field=cat, statistic=statistic, threshold=threshold)

        return styler

    def __str__(self):
        """
        Pretty string representation of a scenario

        """

        scenario_str = f'Required inputs\n{25 * "-"}\n'
        scenario_str = f'{scenario_str}scenario_name = {self.scenario_name}\n'

        if isinstance(self.data, pd.DataFrame):
            data_str = f'data =\n{str(self.data)}\n'
        else:
            data_str = f'{self.data}\n'

        scenario_str = f'{scenario_str}{data_str}'
        scenario_str = f'{scenario_str}in_field = {self.in_field}\n'
        scenario_str = f'{scenario_str}out_field = {self.out_field}\n'
        scenario_str = f'{scenario_str}start_analysis_dt = {self.start_analysis_dt}\n'
        scenario_str = f'{scenario_str}end_analysis_dt = {self.end_analysis_dt}\n\n'

        scenario_str = f'{scenario_str}Frequently used optional inputs\n{35 * "-"}\n'
        scenario_str = f'{scenario_str}cat_field = {self.cat_field}\n'
        scenario_str = f'{scenario_str}bin_size_minutes = {self.bin_size_minutes}\n\n'

        scenario_str = f'{scenario_str}More optional inputs\n{25 * "-"}\n'
        scenario_str = f'{scenario_str}cats_to_exclude = {self.cats_to_exclude}\n'
        scenario_str = f'{scenario_str}occ_weight_field = {self.occ_weight_field}\n'
        scenario_str = f'{scenario_str}percentiles = {self.percentiles}\n'
        scenario_str = f'{scenario_str}los_units = {self.los_units}\n\n'

        scenario_str = f'{scenario_str}Dataframe export options\n{25*"-"}\n'
        scenario_str = f'{scenario_str}export_bydatetime_csv = {self.export_bydatetime_csv}\n'
        scenario_str = f'{scenario_str}export_summaries_csv = {self.export_summaries_csv}\n'
        scenario_str = f'{scenario_str}csv_export_path = {self.csv_export_path}\n\n'

        scenario_str = f'{scenario_str}Macro-level plot options\n{25*"-"}\n'
        scenario_str = f'{scenario_str}make_all_dow_plots = {self.make_all_dow_plots}\n'
        scenario_str = f'{scenario_str}make_all_week_plots = {self.make_all_week_plots}\n'
        scenario_str = f'{scenario_str}export_all_dow_plots = {self.export_all_dow_plots}\n'
        scenario_str = f'{scenario_str}export_all_week_plots = {self.export_all_week_plots}\n'
        scenario_str = f'{scenario_str}plot_export_path = {self.plot_export_path}\n\n'

        scenario_str = f'{scenario_str}Micro-level plot options\n{25*"-"}\n'
        scenario_str = f'{scenario_str}plot_style = {self.plot_style}\n'
        scenario_str = f'{scenario_str}figsize = {self.figsize}\n'
        scenario_str = f'{scenario_str}bar_color_mean = {self.bar_color_mean}\n'
        scenario_str = f'{scenario_str}plot_percentiles = {self.plot_percentiles}\n'
        scenario_str = f'{scenario_str}pctile_color = {self.pctile_color}\n'
        scenario_str = f'{scenario_str}pctile_linestyle = {self.pctile_linestyle}\n'
        scenario_str = f'{scenario_str}pctile_linewidth = {self.pctile_linewidth}\n'
        scenario_str = f'{scenario_str}cap = {self.cap}\n'
        scenario_str = f'{scenario_str}cap_color = {self.cap_color}\n'
        scenario_str = f'{scenario_str}xlabel = {self.xlabel}\n'
        scenario_str = f'{scenario_str}ylabel = {self.ylabel}\n'

        scenario_str = f'{scenario_str}main_title = {self.main_title}\n'
        scenario_str = f'{scenario_str}main_title_properties = {self.main_title_properties}\n'
        scenario_str = f'{scenario_str}subtitle = {self.subtitle}\n'
        scenario_str = f'{scenario_str}subtitle_properties = {self.subtitle_properties}\n'
        scenario_str = f'{scenario_str}legend_properties = {self.legend_properties}\n'
        scenario_str = f'{scenario_str}first_dow = {self.first_dow}\n\n'

        scenario_str = f'{scenario_str}Advanced options\n{25 * "-"}\n'
        scenario_str = f'{scenario_str}edge_bins = {self.edge_bins}\n'
        scenario_str = f'{scenario_str}highres_bin_size_minutes = {self.highres_bin_size_minutes}\n'
        scenario_str = f'{scenario_str}keep_highres_bydatetime = {self.keep_highres_bydatetime}\n'
        scenario_str = f'{scenario_str}nonstationary_stats = {self.nonstationary_stats}\n'
        scenario_str = f'{scenario_str}stationary_stats = {self.stationary_stats}\n'
        scenario_str = f'{scenario_str}verbosity = {self.verbosity}\n\n'



        return scenario_str


def create_scenario(params_dict: Optional[Dict] = None,
                    config_path: Optional[str | Path] = None, **kwargs):
    """Function to create a `Scenario` from a dict, a TOML config file, and/or keyword args """

    # Create empty dict for input parameters
    params = {}

    # If params_dict is not None, merge into params
    if params_dict is not None:
        params.update(params_dict)

    # If toml_path is not None, merge into params
    if config_path is not None:
        with open(config_path, "rb") as f:
            params_toml_dict = tomllib.load(f)
            params = update_params_from_toml(params, params_toml_dict)

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


def update_params_from_toml(params_dict, toml_dict):
    """
    Update dict of input parameters from toml_config dictionary

    Parameters
    ----------
    params_dict : dict
    toml_dict : dict from loading TOML config file

    Returns
    -------
    Updated parameters dict
    """

    # Flatten toml config (we know there are no key clashes and only one nesting level)
    # Update args dict from config dict
    for outerkey, outerval in toml_dict.items():
        for key, val in outerval.items():
            params_dict[key] = val

    return params_dict


# def from_config(config: Path | str):
#     scenario = Scenario.create_scenario(toml_path=config)
#     return scenario
#
#
# def from_dict(params_dict: dict):
#     scenario = Scenario.create_scenario(params_dict=params_dict)
#     return scenario
