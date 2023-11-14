"""
The :mod:`hillmaker.legacy` module provides a function based API for using hillmaker.
"""

# Copyright 2022-2023 Mark Isken, Jacob Norman

from pathlib import Path
from datetime import datetime, date
from typing import Dict

import numpy as np
import pandas as pd

from hillmaker.scenario import create_scenario
from hillmaker.hills import _make_hills


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
        value allowed is 'seconds', largest is 'days'). The default is 'hours'.

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
    alpha : float, optional
        Transparency level for bars. Default = 0.5.
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
        Main title for plot, default = '{Occupancy or Arrivals or Departures} by time of day and day of week'
    main_title_properties : None or dict, optional
        Dict of main title properties, default={{'loc': 'left', 'fontsize': 16}}
    subtitle : str, optional
        subtitle for plot, default = 'Scenario: {scenario_name}'
    subtitle_properties : None or dict, optional
        Dict of subtitle properties, default={'loc': 'left', 'style': 'italic'}
    legend_properties : None or dict, optional
        Dict of legend properties, default={{'loc': 'best', 'frameon': True, 'facecolor': 'w'}}
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

    Example
    -------
    Use like this::

        # Required inputs
        scenario_name = 'ssu_summer24'
        in_field_name = 'InRoomTS'
        out_field_name = 'OutRoomTS'
        start_date = '2024-06-01'
        end_date = '2024-08-31'

        # Optional inputs
        cat_field_name = 'PatType'
        bin_size_minutes = 30
        csv_export_path = './output'

        # Optional plotting inputs
        plot_export_path = './output'
        plot_style = 'default'
        bar_color_mean = 'grey'
        percentiles = [0.85, 0.95]
        plot_percentiles = [0.95, 0.85]
        pctile_color = ['blue', 'green']
        pctile_linewidth = [0.8, 1.0]
        cap = 110
        cap_color = 'black'
        main_title = 'Occupancy summary'
        main_title_properties = {'loc': 'center', 'fontsize':20}
        subtitle = 'Summer 2024 analysis'
        subtitle_properties = {'loc': 'center'}
        xlabel = ''
        ylabel = 'Patients'

        # Optional plotting related inputs

        # Use legacy function interface
        hills = hm.make_hills(scenario_name=scenario_name, data=ssu_stops_df,
                              in_field=in_field_name, out_field=out_field_name,
                              start_analysis_dt=start_date, end_analysis_dt=end_date,
                              cat_field=cat_field_name,
                              bin_size_minutes=bin_size_minutes,
                              csv_export_path=csv_export_path,
                              plot_export_path=plot_export_path, plot_style = plot_style,
                              percentiles=percentiles, plot_percentiles=plot_percentiles,
                              pctile_color=pctile_color, pctile_linewidth=pctile_linewidth,
                              cap=cap, cap_color=cap_color,
                              main_title=main_title, main_title_properties=main_title_properties,
                              subtitle=subtitle, subtitle_properties=subtitle_properties,
                              xlabel=xlabel, ylabel=ylabel
                             )
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



