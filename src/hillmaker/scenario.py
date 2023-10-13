from datetime import datetime, date
from pathlib import Path
import logging
from typing import List, Tuple, Dict, Optional
from enum import IntEnum

import pandas as pd
import numpy as np
from pydantic import BaseModel, field_validator, model_validator, confloat, FieldValidationInfo, ConfigDict

# import hillmaker as hm
from hillmaker.hills import compute_hills_stats, _make_hills, get_plot, get_summary_df, get_bydatetime_df
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
    config : str or Path, optional
        Configuration file (TOML format) containing input parameter arguments and values.
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
       If True, day of week plots are created for occupancy, arrivals, and departures. Default is True.
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
    plot_percentiles : list or tuple of floats (e.g. [0.75, 0.95]), optional
        Which percentiles to plot. Default is (0.95)
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
    los_units: str = 'hours'

    export_bydatetime_csv: bool = False
    export_summaries_csv: bool = False
    csv_export_path: str | Path = Path('.')

    make_all_dow_plots: bool = True
    make_all_week_plots: bool = True
    export_all_dow_plots: bool = False
    export_all_week_plots: bool = False
    plot_export_path: Path | str | None = None

    # Plot options
    plot_style: str = 'ggplot'
    figsize: tuple = (15, 10)
    bar_color_mean: str = 'steelblue'
    plot_percentiles: Tuple[float] | List[float] = (0.95, 0.75)
    pctile_color: Tuple[str] | List[str] = ('black', 'grey')
    pctile_linestyle: Tuple[str] | List[str] = ('-', '--')
    pctile_linewidth: Tuple[float] | List[float] = (0.75, 0.75)
    cap: int | None = None
    cap_color: str = 'r'
    xlabel: str = 'Hour'
    ylabel: str = 'Volume'
    main_title: str = ''
    main_title_properties: None | Dict = {'loc': 'left', 'fontsize': 16}
    subtitle: str = ''
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
    def validate_start_date(cls, v: date | datetime, info: FieldValidationInfo):
        """
        Ensure start date for analysis is convertible to numpy datetime64 and do the conversion.

        Parameters
        ----------
        v
        info

        Returns
        -------

        """

        try:
            start_analysis_dt_ts = pd.Timestamp(v)
            start_analysis_dt_np = start_analysis_dt_ts.to_datetime64()
            return start_analysis_dt_np
        except ValueError as error:
            raise ValueError(f'Cannot convert {v} to to a numpy datetime64 object.\n{error}')

    @field_validator('end_analysis_dt')
    def validate_end_date(cls, v: date | datetime, info: FieldValidationInfo):
        """
        Ensure end date for analysis is convertible to numpy datetime64 and do the conversion.
        Adjust end date to include entire day.

        Parameters
        ----------
        v
        info

        Returns
        -------

        """

        try:
            end_analysis_dt_ts = pd.Timestamp(v).floor("d") + pd.Timedelta(86399, "s")
            end_analysis_dt_np = end_analysis_dt_ts.to_datetime64()
            return end_analysis_dt_np
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

    @field_validator('los_units')
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
    def stop_data(self) -> 'Scenario':
        """If data is a DataFrame return it, else read the csv file into a DataFrame and return that."""
        if isinstance(self.data, pd.DataFrame):
            return self
        else:
            stops_df = pd.read_csv(self.data, parse_dates=[self.in_field, self.out_field])
            self.data = stops_df
            return self

    @model_validator(mode='after')
    def fields_exist(self) -> 'Scenario':
        """Make sure fields exist """

        fields_to_check = [self.in_field, self.out_field, self.cat_field, self.occ_weight_field]
        for field in fields_to_check:
            if field is not None and field not in self.data.columns:
                raise ValueError(f'{field} is not a column in the dataframe')

        return self

    @model_validator(mode='after')
    def date_relationships(self) -> 'Scenario':
        """
        Start date for analysis must be before end date.

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

        return self

    @model_validator(mode='after')
    def bin_size_relationships(self) -> 'Scenario':

        if self.bin_size_minutes < self.highres_bin_size_minutes:
            raise ValueError(
                f'highres_bin_size_minutes ({self.highres_bin_size_minutes}) must be <= bin_size_minutes ({self.bin_size_minutes})')

        if self.edge_bins == EdgeBinsEnum.FRACTIONAL and not self.keep_highres_bydatetime:
            # No need to compute bydatetime at high resolution
            self.highres_bin_size_minutes = self.bin_size_minutes

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
                         plot_percentiles: Tuple[float] | List[float] = (0.95, 0.75),
                         pctile_color: Tuple[str] | List[str] = ('black', 'grey'),
                         pctile_linestyle: Tuple[str] | List[str] = ('-', '--'),
                         pctile_linewidth: Tuple[float] | List[float] = (0.75, 0.75),
                         cap_color: str = 'r',
                         xlabel: str = 'Hour',
                         ylabel: str = 'Volume',
                         main_title: str = '',
                         main_title_properties: None | Dict = {'loc': 'left', 'fontsize': 16},
                         subtitle: str = '',
                         subtitle_properties: None | Dict = {'loc': 'left', 'style': 'italic'},
                         legend_properties: None | Dict = {'loc': 'best', 'frameon': True, 'facecolor': 'w'},
                         first_dow: str = 'mon',
                         plot_export_path: Path | str | None = None, ):

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
                                   plot_percentiles=plot_percentiles,
                                   pctile_color=pctile_color,
                                   pctile_linestyle=pctile_linestyle,
                                   pctile_linewidth=pctile_linewidth,
                                   main_title=main_title,
                                   main_title_properties=main_title_properties,
                                   subtitle=subtitle,
                                   subtitle_properties=subtitle_properties,
                                   legend_properties=legend_properties,
                                   xlabel=xlabel,
                                   ylabel=ylabel,
                                   first_dow=first_dow,
                                   scenario_name=scenario_name,
                                   plot_export_path=plot_export_path)

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
                        xlabel: str = 'Hour',
                        ylabel: str = 'Volume',
                        main_title: str = '',
                        main_title_properties: None | Dict = {'loc': 'left', 'fontsize': 16},
                        subtitle: str = '',
                        subtitle_properties: None | Dict = {'loc': 'left', 'style': 'italic'},
                        legend_properties: None | Dict = {'loc': 'best', 'frameon': True, 'facecolor': 'w'},
                        plot_export_path: Path | str | None = None, ):

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
                                    plot_percentiles=percentiles,
                                    pctile_color=pctile_color,
                                    pctile_linestyle=pctile_linestyle,
                                    pctile_linewidth=pctile_linewidth,
                                    main_title=main_title,
                                    main_title_properties=main_title_properties,
                                    subtitle=subtitle,
                                    subtitle_properties=subtitle_properties,
                                    legend_properties=legend_properties,
                                    xlabel=xlabel,
                                    ylabel=ylabel,
                                    scenario_name=scenario_name,
                                    plot_export_path=plot_export_path)

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
        """Pretty string representation of a scenario"""
        # TODO - write str method for Scenario class
        return str(self.model_dump())

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

        # Read in stop data to DataFrame if needed
        #stops_df = pd.read_csv(params['stop_data_csv'], parse_dates=[params['in_field'], params['out_field']])
        #params['stops_df'] = stops_df
        # Remove the csv key
        #params.pop('stop_data_csv', None)

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


def from_config(config: Path | str):
    scenario = Scenario.create_scenario(toml_path=config)
    return scenario


def from_dict(params_dict: dict):
    scenario = Scenario.create_scenario(params_dict=params_dict)
    return scenario