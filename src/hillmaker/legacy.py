from typing import Tuple, List
from pathlib import Path
from datetime import datetime, date
from typing import Dict

import numpy as np
import pandas as pd

from hillmaker.scenario import Scenario, VerbosityEnum
from hillmaker.hills import _make_hills
from hillmaker.utils import create_scenario


def make_hills(scenario_name: str = None,
               data: str | Path | pd.DataFrame = None,
               in_field: str = None, out_field: str = None,
               start_analysis_dt: str | date | datetime | pd.Timestamp | np.datetime64 = None,
               end_analysis_dt: str | date | datetime | pd.Timestamp | np.datetime64 = None,
               cat_field: str = None,
               bin_size_minutes: int = 60,
               export_bydatetime_csv: bool = True,
               export_summaries_csv: bool = True,
               csv_export_path: str | Path = Path('./'),
               make_all_dow_plots: bool = True,
               make_all_week_plots: bool = True,
               export_all_dow_plots: bool = False,
               export_all_week_plots: bool = False,
               plot_export_path: str | Path = Path('./'),
               **kwargs) -> Dict:
    """
    Compute occupancy, arrival, and departure statistics by category, time bin of day and day of week.

    Main function that first calls `bydatetime.make_bydatetime` to calculate occupancy, arrival
    and departure values by date by time bin and then calls `summarize.summarize`
    to compute the summary statistics.

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
        Destination path for exported csv files, default is the current directory

    make_all_dow_plots : bool, optional
       If True, day of week plots are created for occupancy, arrival, and departure. Default is True.
    make_all_week_plots : bool, optional
       If True, full week plots are created for occupancy, arrival, and departure. Default is True.
    export_all_dow_plots : bool, optional
       If True, day of week plots are exported for occupancy, arrival, and departure. Default is False.
    export_all_week_plots : bool, optional
       If True, full week plots are exported for occupancy, arrival, and departure. Default is False.
    plot_export_path : str or Path, optional, default is the current directory
        Destination path for exported png files, default is the current directory

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


    Returns
    -------
    dict of DataFrames and plots
       The bydatetime DataFrames, all summary DataFrames and any plots created.
        """

    # Add named args to kwargs
    kwargs['scenario_name'] = scenario_name
    kwargs['data'] = data
    kwargs['in_field'] = in_field
    kwargs['out_field'] = out_field
    kwargs['start_analysis_dt'] = start_analysis_dt
    kwargs['end_analysis_dt'] = end_analysis_dt
    kwargs['cat_field'] = cat_field
    kwargs['bin_size_minutes'] = bin_size_minutes

    kwargs['export_bydatetime_csv'] = export_bydatetime_csv
    kwargs['export_summaries_csv'] = export_summaries_csv
    kwargs['csv_export_path'] = csv_export_path
    kwargs['make_all_dow_plots'] = make_all_dow_plots
    kwargs['make_all_week_plots'] = make_all_week_plots
    kwargs['export_all_dow_plots'] = export_all_dow_plots
    kwargs['export_all_week_plots'] = export_all_week_plots
    kwargs['plot_export_path'] = plot_export_path


    # Check if config filename passed in
    if 'config' in kwargs:
        config = kwargs['config']
        kwargs.pop('config', None)
        scenario = create_scenario(kwargs, config)
    else:
        scenario = create_scenario(kwargs)

    hills = _make_hills(scenario)
    return hills


def make_hills_allparams(scenario_name: str,
                         stops_df: pd.DataFrame,
                         in_field: str, out_field: str,
                         start_analysis_dt: str | date | datetime | pd.Timestamp | np.datetime64,
                         end_analysis_dt: str | date | datetime | pd.Timestamp | np.datetime64,
                         config: str | Path = None,
                         cat_field: str = None,
                         bin_size_minutes: int = 60,
                         percentiles: Tuple | List = (0.25, 0.5, 0.75, 0.95, 0.99),
                         cats_to_exclude: str | None = None,
                         occ_weight_field: str | None = None,
                         cap: int | None = None,
                         los_units: str = 'hours',
                         csv_export_path: str | Path = Path('.'),
                         export_bydatetime_csv: bool = True,
                         export_summaries_csv: bool = True,
                         make_all_dow_plots: bool = True,
                         make_all_week_plots: bool = True,
                         export_all_dow_plots: bool = False,
                         export_all_week_plots: bool = False,
                         plot_export_path: Path | str | None = None,
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

                         edge_bins: int = 1,
                         highres_bin_size_minutes: int = 5,
                         keep_highres_bydatetime: bool = False,
                         nonstationary_stats: bool = True,
                         stationary_stats: bool = True,
                         verbosity: int = VerbosityEnum.INFO,
                         ) -> Dict:
    """
    Compute occupancy, arrival, and departure statistics by category, time bin of day and day of week.

    Main function that first calls `bydatetime.make_bydatetime` to calculate occupancy, arrival
    and departure values by date by time bin and then calls `summarize.summarize`
    to compute the summary statistics.

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
       If True, day of week plots are created for occupancy, arrival, and departure. Default is True.
    make_all_week_plots : bool, optional
       If True, full week plots are created for occupancy, arrival, and departure. Default is True.
    export_all_dow_plots : bool, optional
       If True, day of week plots are exported for occupancy, arrival, and departure. Default is False.
    export_all_week_plots : bool, optional
       If True, full week plots are exported for occupancy, arrival, and departure. Default is False.
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


    Returns
    -------
    dict of DataFrames and plots
       The bydatetime DataFrames, all summary DataFrames and any plots created.
    """

    # Create scenario instance so that validation and preprocessing get done

    scenario = Scenario(scenario_name=scenario_name, stops_df=stops_df,
                        in_field=in_field, out_field=out_field,
                        start_analysis_dt=start_analysis_dt, end_analysis_dt=end_analysis_dt,
                        config=config,
                        cat_field=cat_field,
                        bin_size_minutes=bin_size_minutes,
                        cats_to_exclude=cats_to_exclude, occ_weight_field=occ_weight_field,
                        edge_bins=edge_bins,
                        percentiles=percentiles, los_units=los_units,
                        csv_export_path=csv_export_path,
                        cap=cap,
                        make_all_dow_plots=make_all_dow_plots, make_all_week_plots=make_all_week_plots,
                        export_bydatetime_csv=export_bydatetime_csv,
                        export_summaries_csv=export_summaries_csv,
                        export_all_dow_plots=export_all_dow_plots,
                        export_all_week_plots=export_all_week_plots,
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
                        plot_export_path=plot_export_path,
                        highres_bin_size_minutes=highres_bin_size_minutes,
                        keep_highres_bydatetime=keep_highres_bydatetime,
                        stationary_stats=stationary_stats, nonstationary_stats=nonstationary_stats,
                        verbosity=verbosity)

    hills = _make_hills(scenario)
    return hills
