"""
The :mod:`hillmaker.plotting` module includes functions for creating daily and weekly plots.
"""

# Copyright 2022-2023 Mark Isken, Jacob Norman

import logging
from typing import Tuple, List, Dict
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from cycler import cycler

# from hillmaker.scenario import Scenario
from hillmaker.hmlib import HillTimer, pctile_field_name

# if typing.TYPE_CHECKING:
#     from hillmaker.scenario import Scenario


def _plot_dow(dow, first_dow):
    if dow < first_dow:
        return dow + 7
    else:
        return dow


def _metric_name(metric, capitalize=True):
    """
    Get optionally capitalized metric name from metric abbreviation.

    Parameters
    ----------
    metric : str
        Some abbreviated version of occupancy, arrivals or departures
    capitalize : bool
        Capitalize first letter if True, default is True

    Returns
    -------
    str

    """

    metric_name_map = {'o': 'occupancy', 'a': 'arrivals', 'd': 'departures'}
    metric_name = metric_name_map[metric.lower()[0]]
    if capitalize:
        metric_name = metric_name.title()
    return metric_name


def _dow_name(dow, capitalize=True):
    """
    Get optionally capitalized metric name from day of week abbreviation.

    Parameters
    ----------
    capitalize : bool
        Capitalize first letter if True, default is True

    Returns
    -------
    str

    """

    dow_name_map = {'mon': 'monday', 'tue': 'tuesday', 'wed': 'wednesday', 'thu': 'thursday',
                    'fri': 'friday', 'sat': 'saturday', 'sun': 'sunday'}
    dow_name = dow_name_map[dow.lower()[:3]]
    if capitalize:
        dow_name = dow_name.title()
    return dow_name


def make_plots(scenario, hills: dict):
    """
    Create weekly and all dow plots for arrivals, departures, and occupancy

    Parameters
    ----------
    scenario : Scenario
    hills : dict

    Returns
    -------
    dict of matplotlib plot objects

    """
    # Logging
    # This should inherit level from root logger
    logger = logging.getLogger(__name__)

    # Create and export full week plots if requested
    plots = {}
    if scenario.make_all_week_plots or scenario.export_all_week_plots:
        with HillTimer() as t:
            for metric in hills['summaries']['nonstationary']['dow_binofday']:
                fullwk_df = hills['summaries']['nonstationary']['dow_binofday'][metric]

                week_range_str = 'week'
                plot_key = f'{scenario.scenario_name}_{metric}_plot_{week_range_str}'

                if scenario.export_all_week_plots:
                    plot_export_path = scenario.plot_export_path
                else:
                    plot_export_path = None

                plot = make_week_hill_plot(fullwk_df, scenario_name=scenario.scenario_name, metric=metric,
                                           bin_size_minutes=scenario.bin_size_minutes,
                                           cap=scenario.cap, cap_color=scenario.cap_color,
                                           plot_style=scenario.plot_style,
                                           figsize=scenario.figsize,
                                           bar_color_mean=scenario.bar_color_mean,
                                           plot_percentiles=scenario.plot_percentiles,
                                           pctile_color=scenario.pctile_color,
                                           pctile_linestyle=scenario.pctile_linestyle,
                                           pctile_linewidth=scenario.pctile_linewidth,
                                           main_title=scenario.main_title,
                                           main_title_properties=scenario.main_title_properties,
                                           subtitle=scenario.subtitle,
                                           subtitle_properties=scenario.subtitle_properties,
                                           legend_properties=scenario.legend_properties,
                                           xlabel=scenario.xlabel,
                                           ylabel=scenario.ylabel,
                                           first_dow=scenario.first_dow,
                                           plot_export_path=plot_export_path)

                plots[plot_key] = plot

        logger.info(f"Full week plots created (seconds): {t.interval:.4f}")

    # Create and export individual day of week plots if requested
    if scenario.make_all_dow_plots or scenario.export_all_dow_plots:
        with HillTimer() as t:
            for metric in hills['summaries']['nonstationary']['dow_binofday']:
                fullwk_df = hills['summaries']['nonstationary']['dow_binofday'][metric]
                for dow in fullwk_df['dow_name'].unique():
                    dow_df = fullwk_df.loc[fullwk_df['dow_name'] == dow]
                    week_range_str = dow
                    plot_key = f'{scenario.scenario_name}_{metric}_plot_{week_range_str}'

                    if scenario.export_all_dow_plots:
                        plot_export_path = scenario.plot_export_path
                    else:
                        plot_export_path = None
                    plot = make_daily_hill_plot(dow_df, dow.lower(), scenario_name=scenario.scenario_name,
                                                metric=metric,
                                                bin_size_minutes=scenario.bin_size_minutes,
                                                cap=scenario.cap,
                                                cap_color=scenario.cap_color,
                                                plot_style=scenario.plot_style,
                                                figsize=scenario.figsize,
                                                bar_color_mean=scenario.bar_color_mean,
                                                plot_percentiles=scenario.plot_percentiles,
                                                pctile_color=scenario.pctile_color,
                                                pctile_linestyle=scenario.pctile_linestyle,
                                                pctile_linewidth=scenario.pctile_linewidth,
                                                main_title=scenario.main_title,
                                                main_title_properties=scenario.main_title_properties,
                                                subtitle=scenario.subtitle,
                                                subtitle_properties=scenario.subtitle_properties,
                                                legend_properties=scenario.legend_properties,
                                                xlabel=scenario.xlabel,
                                                ylabel=scenario.ylabel,
                                                plot_export_path=plot_export_path)
                    plots[plot_key] = plot

        logger.info(f"Individual day of week plots created (seconds): {t.interval:.4f}")

    return plots


def make_week_hill_plot(summary_df: pd.DataFrame, metric: str = 'occupancy',
                        bin_size_minutes: int = 60,
                        cap: int = None,
                        plot_style: str = 'ggplot',
                        figsize: tuple = (15, 10),
                        bar_color_mean: str = 'steelblue',
                        alpha: float = 0.5,
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
                        scenario_name: str = '',
                        plot_export_path: Path | str | None = None, ):
    f"""
    Makes and optionally exports week plot for occupancy, arrivals, or departures.

    Takes output DataFrames of `summarize.summarize` and plots mean and percentile
    values for occupancy, arrival, and departure categories.

    Parameters
    ----------
    summary_df : DataFrame
        Single summary df from the output of `summarize.summarize`
    metric : str
        One of 'occupancy', 'arrivals', 'departures'
    plot_style : str, optional
        Matplotlib built in style name. Default is 'ggplot'.
    figsize : Tuple, optional
        Figure size. Default is (15, 10)
    bar_color_mean : str, optional
        Matplotlib color name for the bars representing mean values. Default is 'steelblue'
    alpha: float, optional
        Value between 0 and 1 specifying the opacity of the mean bars. Default is 0.5
    plot_percentiles : list or tuple of floats (e.g. [0.75, 0.95]), optional
        Which percentiles to plot. Default is (0.95)
    pctile_color : list or tuple of color codes (e.g. ['blue', 'green'] or list('gb'), optional
        Line color for each percentile series plotted. Order should match order of percentiles list.
        Default is ('black', 'grey').
    pctile_linestyle : List or tuple of line styles (e.g. ['-', '--']), optional
        Line style for each percentile series plotted. Default is ('-', '--').
    pctile_linewidth : List or tuple of line widths in points (e.g. [1.0, 0.75])
        Line width for each percentile series plotted. Default is (0.75, 0.75).
    bin_size_minutes : int, optional
        Number of minutes in each time bin of the day, default is 60. Use a value that
        divides into 1440 with no remainder
    cap : int, optional
        Capacity of area being analyzed, default is None
    cap_color : str, optional
        matplotlib color code, default='r'
    xlabel : str, optional
        x-axis label, default='Hour'
    ylabel : str, optional
        y-axis label, default='Volume'
    main_title : str, optional
        main title for plot, default = ''
    main_title_properties : None or dict, optional
        Dict of `title` properties, default={{'loc': 'left', 'fontsize': 16}}
    subtitle : str, optional
        subtitle for plot, default = ''
    subtitle_properties : None or dict, optional
        Dict of subtitle properties, default={{'loc': 'left', 'style': 'italic'}}
    legend_properties : None or dict, optional
        Dict of `legend` properties, default={{'loc': 'best', 'frameon': True, 'facecolor': 'w'}}
    first_dow : str, optional
        Controls which day of week appears first in plot. One of 'mon', 'tue', 'wed', 'thu', 'fri', 'sat, 'sun'
    scenario_name : str
        Used in output filenames, default is ''
    plot_export_path : str or None, default is None
        If not None, plot is exported to `export_path`
    """

    # Create default titles
    if main_title == '':
        main_title = f'{_metric_name(metric)} by time of day and day of week'

    if subtitle == '':
        if len(scenario_name) > 0:
            subtitle = f'Scenario: {scenario_name}'
            main_title += '\n'  # appends newline character to make room for subtitle
    else:
        main_title += '\n'  # appends newline character to make room for subtitle

    with plt.style.context(plot_style):
        # Create empty sized figure
        fig1 = plt.figure(figsize=figsize)
        ax1 = fig1.add_subplot(1, 1, 1)

        # infer number of days being plotted
        num_days = len(summary_df) / (60 / bin_size_minutes * 24)

        # Create a list to use as the X-axis values
        num_bins = num_days * 1440 / bin_size_minutes
        base_dates = {'sun': '2015-01-04', 'mon': '2015-01-05', 'tue': '2015-01-06',
                      'wed': '2015-01-07', 'thu': '2015-01-08', 'fri': '2015-01-09', 'sat': '2015-01-10'}
        first_dow_map = {'sun': 6, 'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5}
        first_dow_val = first_dow_map[first_dow]
        # Adjust the axis labels for first_dow
        base_date_for_first_dow = base_dates[first_dow]
        timestamps = pd.date_range(base_date_for_first_dow, periods=num_bins, freq=f'{bin_size_minutes}Min').tolist()
        # Adjust the summary df for first_dow
        occ_summary_df_plot = summary_df.copy()
        occ_summary_df_plot['plot_dow'] = occ_summary_df_plot['day_of_week'].map(lambda d: _plot_dow(d, first_dow_val))
        occ_summary_df_plot.sort_values(by=['plot_dow', 'bin_of_day'], inplace=True)

        # Choose appropriate major and minor tick locations
        major_tick_locations = pd.date_range(f'{base_date_for_first_dow} 12:00:00', periods=7, freq='24H').tolist()
        minor_tick_locations = pd.date_range(f'{base_date_for_first_dow} 06:00:00', periods=42, freq='4H').tolist()

        # Set the tick locations for the axes object
        ax1.set_xticks(major_tick_locations)
        ax1.set_xticks(minor_tick_locations, minor=True)

        # Add data to the plot
        # Mean occupancy as bars - here's the GOTCHA involving the bar width
        bar_width = 1 / (1440 / bin_size_minutes)
        ax1.bar(timestamps, occ_summary_df_plot['mean'], label=f'Mean {metric}',
                width=bar_width, color=bar_color_mean, edgecolor=None, alpha=alpha)

        # Percentiles as lines
        # Style the line for the occupancy percentile
        cycler_pctiles = \
            cycler(color=pctile_color) + cycler(linestyle=pctile_linestyle) + cycler(linewidth=pctile_linewidth)
        ax1.set_prop_cycle(cycler_pctiles)

        for p in plot_percentiles:
            pct_name = pctile_field_name(p)
            label = f'{pct_name[1:]}th %ile {metric}'
            ax1.plot(timestamps, occ_summary_df_plot[pct_name], label=label)

        # establish capacity horizontal line if supplied
        if cap is not None and metric.lower()[0] == 'o':
            ax1.axhline(cap, color=cap_color, linestyle='--', label='Capacity')

        # Create formatter variables
        day_fmt = '' if num_days == 1 else '%a'
        dayofweek_formatter = DateFormatter(day_fmt)
        qtrday_formatter = DateFormatter('%H')

        # Format the tick labels
        ax1.xaxis.set_major_formatter(dayofweek_formatter)
        ax1.xaxis.set_minor_formatter(qtrday_formatter)

        # Slide the major tick labels underneath the default location by 20 points
        ax1.tick_params(which='major', pad=20)

        # Add other chart elements

        # Set plot and axis titles
        # Be nice to have application and session level defaults - style sheets for app level?
        if main_title_properties is None:
            main_title_properties = {}

        # Create an invisible subplot to add the second title
        ax2 = fig1.add_axes(ax1.get_position(), zorder=1, frame_on=False)
        ax2.set_axis_off()
        ax2.set_title(main_title, **main_title_properties)

        if subtitle_properties is None:
            subtitle_properties = {}
        ax1.set_title(subtitle, **subtitle_properties)

        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)

        # Legend
        if legend_properties is not None:
            ax1.legend(**legend_properties)

        # save figure
        if plot_export_path is not None:
            week_range_str = 'week'
            plot_png = f'{scenario_name}_{metric}_{week_range_str}.png'
            png_wpath = Path(plot_export_path, plot_png)
            plt.savefig(png_wpath, bbox_inches='tight')

        # Suppress plot output in notebook
        plt.close()

    return fig1


def make_week_combo_plot(summary_df1: pd.DataFrame,
                         summary_df2: pd.DataFrame,
                         metric1: str = 'arrivals',
                         metric2: str = 'occupancy',
                         bin_size_minutes: int = 60,
                         plot_style: str = 'ggplot',
                         figsize: tuple = (15, 10),
                         bar_color_mean: str = 'steelblue',
                         alpha: float = 0.5,
                         percentiles: Tuple[float] | List[float] = (0.95, 0.75),
                         pctile_color: Tuple[str] | List[str] = ('black', 'grey'),
                         pctile_linestyle: Tuple[str] | List[str] = ('-', '--'),
                         pctile_linewidth: Tuple[float] | List[float] = (0.75, 0.75),
                         xlabel: str = 'Hour',
                         ylabel: str = 'Volume',
                         main_title: str = '',
                         main_title_properties: None | Dict = {'loc': 'left', 'fontsize': 16},
                         subtitle: str = '',
                         subtitle_properties: None | Dict = {'loc': 'left', 'style': 'italic'},
                         legend_properties: None | Dict = {'loc': 'best', 'frameon': True, 'facecolor': 'w'},
                         first_dow: str = 'mon',
                         scenario_name: str = '',
                         plot_export_path: Path | str | None = None, ):
    f"""
    Makes and optionally exports week plot for two metrics (occupancy, arrivals, or departures) simultaneously.

    Takes output DataFrames of `summarize.summarize` and plots mean and percentile
    values for occupancy, arrival, and departure categories.

    Parameters
    ----------
    summary_df1 : DataFrame
        Single summary df from the output of `summarize.summarize`. Will be mean bars of plot.
    summary_df2 : DataFrame
        Single summary df from the output of `summarize.summarize`. Will be percentile lines of plot.
    metric1 : str
        One of 'occupancy', 'arrivals', 'departures' that corresponds to `summary_df1`. Default is 'arrivals'.
    metric2 : str
        One of 'occupancy', 'arrivals', 'departures' that corresponds to `summary_df2`. Default is 'occupancy'.
    plot_style : str, optional
        Matplotlib built in style name. Default is 'ggplot'.
    figsize : Tuple, optional
        Figure size. Default is (15, 10)
    bar_color_mean : str, optional
        Matplotlib color name for the bars representing mean values. Default is 'steelblue'
    alpha: float, optional
        Value between 0 and 1 specifying the opacity of the mean bars. Default is 0.5
    percentiles : list or tuple of floats (e.g. [0.75, 0.95]), optional
        Which percentiles to plot. Default is (0.95)
    pctile_color : list or tuple of color codes (e.g. ['blue', 'green'] or list('gb'), optional
        Line color for each percentile series plotted. Order should match order of percentiles list.
        Default is ('black', 'grey').
    pctile_linestyle : List or tuple of line styles (e.g. ['-', '--']), optional
        Line style for each percentile series plotted. Default is ('-', '--').
    pctile_linewidth : List or tuple of line widths in points (e.g. [1.0, 0.75])
        Line width for each percentile series plotted. Default is (0.75, 0.75).
    bin_size_minutes : int, optional
        Number of minutes in each time bin of the day, default is 60. Use a value that
        divides into 1440 with no remainder
    xlabel : str, optional
        x-axis label, default='Hour'
    ylabel : str, optional
        y-axis label, default='Volume'
    main_title : str, optional
        Main title for plot, default = ''
    main_title_properties : None or dict, optional
        Dict of `title` properties, default={{'loc': 'left', 'fontsize': 16}}
    subtitle : str, optional
        subtitle for plot, default = ''
    subtitle_properties : None or dict, optional
        Dict of `title` properties, default={{'loc': 'left', 'style': 'italic'}}
    legend_properties : None or dict, optional
        Dict of `legend` properties, default={{'loc': 'best', 'frameon': True, 'facecolor': 'w'}}
    first_dow : str, optional
        Controls which day of week appears first in plot. One of 'mon', 'tue', 'wed', 'thu', 'fri', 'sat, 'sun'
    scenario_name : str
        Used in output filenames, default is ''
    plot_export_path : str or None, default is None
        If not None, plot is exported to `export_path`
    """

    # Create default titles
    if main_title == '':
        main_title = f'{_metric_name(metric1)} & {_metric_name(metric2).lower()} by time of day and day of week'

    if subtitle == '':
        if len(scenario_name) > 0:
            subtitle = f'Scenario: {scenario_name}'
            main_title += '\n'  # appends newline character to make room for subtitle
    else:
        main_title += '\n'  # appends newline character to make room for subtitle

    with plt.style.context(plot_style):
        # Create empty sized figure
        fig1 = plt.figure(figsize=figsize)
        ax1 = fig1.add_subplot(1, 1, 1)

        # infer number of days being plotted
        num_days = len(summary_df1) / (60 / bin_size_minutes * 24)

        # Create a list to use as the X-axis values
        num_bins = num_days * 1440 / bin_size_minutes
        base_dates = {'sun': '2015-01-04', 'mon': '2015-01-05', 'tue': '2015-01-06',
                      'wed': '2015-01-07', 'thu': '2015-01-08', 'fri': '2015-01-09', 'sat': '2015-01-10'}
        first_dow_map = {'sun': 6, 'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5}
        first_dow_val = first_dow_map[first_dow]
        # Adjust the axis labels for first_dow
        base_date_for_first_dow = base_dates[first_dow]
        timestamps = pd.date_range(base_date_for_first_dow, periods=num_bins, freq=f'{bin_size_minutes}Min').tolist()

        # Adjust the summary df for first_dow
        arr_summary_df_plot = summary_df1.copy()
        arr_summary_df_plot['plot_dow'] = arr_summary_df_plot['day_of_week'].map(lambda d: _plot_dow(d, first_dow_val))
        arr_summary_df_plot.sort_values(by=['plot_dow', 'bin_of_day'], inplace=True)

        # Adjust the summary df for first_dow
        occ_summary_df_plot = summary_df2.copy()
        occ_summary_df_plot['plot_dow'] = occ_summary_df_plot['day_of_week'].map(lambda d: _plot_dow(d, first_dow_val))
        occ_summary_df_plot.sort_values(by=['plot_dow', 'bin_of_day'], inplace=True)

        # Choose appropriate major and minor tick locations
        major_tick_locations = pd.date_range(f'{base_date_for_first_dow} 12:00:00', periods=7, freq='24H').tolist()
        minor_tick_locations = pd.date_range(f'{base_date_for_first_dow} 06:00:00', periods=42, freq='4H').tolist()

        # Set the tick locations for the axes object
        ax1.set_xticks(major_tick_locations)
        ax1.set_xticks(minor_tick_locations, minor=True)

        # Add data to the plot
        # Mean occupancy as bars - here's the GOTCHA involving the bar width
        bar_width = 1 / (1440 / bin_size_minutes)
        ax1.bar(timestamps, arr_summary_df_plot['mean'], label=f'Mean {metric1}',
                width=bar_width, color=bar_color_mean, edgecolor=None, alpha=alpha)

        # Percentiles as lines
        # Style the line for the occupancy percentile
        cycler_pctiles = \
            cycler(color=pctile_color) + cycler(linestyle=pctile_linestyle) + cycler(linewidth=pctile_linewidth)
        ax1.set_prop_cycle(cycler_pctiles)

        for p in percentiles:
            pct_name = pctile_field_name(p)
            label = f'{pct_name[1:]}th %ile {metric2}'
            ax1.plot(timestamps, occ_summary_df_plot[pct_name], label=label)

        # Create formatter variables
        day_fmt = '' if num_days == 1 else '%a'
        dayofweek_formatter = DateFormatter(day_fmt)
        qtrday_formatter = DateFormatter('%H')

        # Format the tick labels
        ax1.xaxis.set_major_formatter(dayofweek_formatter)
        ax1.xaxis.set_minor_formatter(qtrday_formatter)

        # Slide the major tick labels underneath the default location by 20 points
        ax1.tick_params(which='major', pad=20)

        # Add other chart elements

        # Set plot and axis titles
        # Be nice to have application and session level defaults - style sheets for app level?
        if main_title_properties is None:
            main_title_properties = {}

        # Create an invisible subplot to add the second title
        ax2 = fig1.add_axes(ax1.get_position(), zorder=1, frame_on=False)
        ax2.set_axis_off()
        ax2.set_title(main_title, **main_title_properties)

        if subtitle_properties is None:
            subtitle_properties = {}
        ax1.set_title(subtitle, **subtitle_properties)

        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)

        # Legend
        if legend_properties is not None:
            ax1.legend(**legend_properties)

        # save figure
        if plot_export_path is not None:
            week_range_str = 'week'
            plot_png = f'{scenario_name}_{metric1}_{metric2}_{week_range_str}.png'
            png_wpath = Path(plot_export_path, plot_png)
            plt.savefig(png_wpath, bbox_inches='tight')

        # Suppress plot output in notebook
        plt.close()

    return fig1


def make_daily_hill_plot(summary_df: pd.DataFrame, day_of_week: str, metric: str = 'occupancy',
                         bin_size_minutes: int = 60,
                         cap: int = None,
                         plot_style: str = 'ggplot',
                         figsize: tuple = (15, 10),
                         bar_color_mean: str = 'steelblue',
                         alpha: float = 0.5,
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
                         scenario_name: str = '',
                         plot_export_path: Path | str | None = None, ):
    f"""
    Makes and optionally exports week plot for occupancy, arrivals, or departures.

    Takes output DataFrames of `summarize.summarize` and plots mean and percentile
    values for occupancy, arrival, and departure categories.

    Parameters
    ----------
    summary_df : DataFrame
        Single summary df from the output of `summarize.summarize`
    day_of_week : str
        One of 'mon', 'tue', 'wed', 'thu', 'fri', 'sat, 'sun'
    metric : str
        One of 'occupancy', 'arrivals', 'departures'
    plot_style : str, optional
        Matplotlib built in style name. Default is 'ggplot'.
    figsize : Tuple, optional
        Figure size. Default is (15, 10)
    bar_color_mean : str, optional
        Matplotlib color name for the bars representing mean values. Default is 'steelblue'
    alpha: float, optional
        Value between 0 and 1 specifying the opacity of the mean bars. Default is 0.5
    plot_percentiles : list or tuple of floats (e.g. [0.75, 0.95]), optional
        Which percentiles to plot. Default is (0.95)
    pctile_color : list or tuple of color codes (e.g. ['blue', 'green'] or list('gb'), optional
        Line color for each percentile series plotted. Order should match order of percentiles list.
        Default is ('black', 'grey').
    pctile_linestyle : List or tuple of line styles (e.g. ['-', '--']), optional
        Line style for each percentile series plotted. Default is ('-', '--').
    pctile_linewidth : List or tuple of line widths in points (e.g. [1.0, 0.75])
        Line width for each percentile series plotted. Default is (0.75, 0.75).
    bin_size_minutes : int, optional
        Number of minutes in each time bin of the day, default is 60. Use a value that
        divides into 1440 with no remainder
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
    scenario_name : str
        Used in output filenames, default is ''
    plot_export_path : str or None, default is None
        If not None, plot is exported to `export_path`
    """

    # Create default titles
    if main_title == '':
        main_title = f'{_metric_name(metric)} summary - {_dow_name(day_of_week)}'

    if subtitle == '':
        if len(scenario_name) > 0:
            subtitle = f'Scenario: {scenario_name}'
            main_title += '\n'  # appends newline character to make room for subtitle
    else:
        main_title += '\n'  # appends newline character to make room for subtitle

    with plt.style.context(plot_style):
        # Create empty sized figure
        fig1 = plt.figure(figsize=figsize)
        ax1 = fig1.add_subplot(1, 1, 1)

        num_days = 1

        # Create a list to use as the X-axis values
        num_bins = num_days * 1440 / bin_size_minutes
        base_dates = {'sun': '2015-01-04', 'mon': '2015-01-05', 'tue': '2015-01-06',
                      'wed': '2015-01-07', 'thu': '2015-01-08', 'fri': '2015-01-09', 'sat': '2015-01-10'}
        dow_map = {'sun': 6, 'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5}
        dow_val = dow_map[day_of_week]
        # Adjust the axis labels for first_dow
        base_date_for_first_dow = base_dates[day_of_week]
        timestamps = pd.date_range(base_date_for_first_dow, periods=num_bins, freq=f'{bin_size_minutes}Min').tolist()
        # Adjust the summary df for dow to plot
        occ_summary_df_plot = summary_df.copy()
        occ_summary_df_plot = occ_summary_df_plot[occ_summary_df_plot['day_of_week'] == dow_val].copy()
        occ_summary_df_plot.sort_values(by=['bin_of_day'], inplace=True)

        # Choose appropriate major and minor tick locations
        major_tick_locations = pd.date_range(f'{base_date_for_first_dow} 00:00:00', periods=24, freq='1H').tolist()
        # minor_tick_locations = pd.date_range(f'{base_date_for_first_dow} 01:00:00', periods=24, freq='1H').tolist()

        # Set the tick locations for the axes object
        ax1.set_xticks(major_tick_locations)

        # Add data to the plot
        # Mean occupancy as bars - here's the GOTCHA involving the bar width
        bar_width = 1 / (1440 / bin_size_minutes)
        ax1.bar(timestamps, occ_summary_df_plot['mean'], label=f'Mean {metric}',
                width=bar_width, color=bar_color_mean, edgecolor=None, alpha=alpha)

        # Percentiles as lines
        # Style the line for the occupancy percentile
        cycler_pctiles = (
                cycler(color=pctile_color) + cycler(linestyle=pctile_linestyle) + cycler(linewidth=pctile_linewidth))
        ax1.set_prop_cycle(cycler_pctiles)

        for p in plot_percentiles:
            pct_name = pctile_field_name(p)
            label = f'{pct_name[1:]}th %ile {metric}'
            ax1.plot(timestamps, occ_summary_df_plot[pct_name], label=label)

        # establish capacity horizontal line if supplied
        if cap is not None and metric.lower()[0] == 'o':
            ax1.axhline(cap, color=cap_color, linestyle='--', label='Capacity')

        # Create formatter variables
        # day_fmt = '' if num_days == 1 else '%a'
        # dayofweek_formatter = DateFormatter(day_fmt)
        hour_formatter = DateFormatter('%H')

        # Format the tick labels
        ax1.xaxis.set_major_formatter(hour_formatter)

        # Slide the major tick labels underneath the default location by 20 points
        # ax1.tick_params(which='major', pad=20)

        # Add other chart elements

        # Set plot and axis titles
        # Be nice to have application and session level defaults - style sheets for app level?
        if main_title_properties is None:
            main_title_properties = {}

        # Create an invisible subplot to add the second title
        ax2 = fig1.add_axes(ax1.get_position(), zorder=1, frame_on=False)
        ax2.set_axis_off()
        ax2.set_title(main_title, **main_title_properties)

        if subtitle_properties is None:
            subtitle_properties = {}
        ax1.set_title(subtitle, **subtitle_properties)

        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)

        # Legend
        if legend_properties is not None:
            ax1.legend(**legend_properties)

        # save figure
        if plot_export_path is not None:
            week_range_str = day_of_week
            plot_png = f'{scenario_name}_{metric}_{week_range_str}.png'
            png_wpath = Path(plot_export_path, plot_png)
            plt.savefig(png_wpath, bbox_inches='tight')

        # Suppress plot output in notebook
        plt.close()

    return fig1


def make_daily_combo_plot(summary_df1: pd.DataFrame,
                          summary_df2: pd.DataFrame,
                          day_of_week: str,
                          metric1: str = 'arrivals',
                          metric2: str = 'occupancy',
                          bin_size_minutes: int = 60,
                          plot_style: str = 'ggplot',
                          figsize: tuple = (15, 10),
                          bar_color_mean: str = 'steelblue',
                          alpha: float = 0.5,
                          percentiles: Tuple[float] | List[float] = (0.95, 0.75),
                          pctile_color: Tuple[str] | List[str] = ('black', 'grey'),
                          pctile_linestyle: Tuple[str] | List[str] = ('-', '--'),
                          pctile_linewidth: Tuple[float] | List[float] = (0.75, 0.75),
                          xlabel: str = 'Hour',
                          ylabel: str = 'Volume',
                          main_title: str = '',
                          main_title_properties: None | Dict = {'loc': 'left', 'fontsize': 16},
                          subtitle: str = '',
                          subtitle_properties: None | Dict = {'loc': 'left', 'style': 'italic'},
                          legend_properties: None | Dict = {'loc': 'best', 'frameon': True, 'facecolor': 'w'},
                          scenario_name: str = '',
                          export_path: Path | str | None = None, ):
    f"""
    Makes and optionally exports week plot for two metrics (occupancy, arrivals, or departures) simultaneously.

    Takes output DataFrames of `summarize.summarize` and plots mean and percentile
    values for occupancy, arrival, and departure categories.

    Parameters
    ----------
    summary_df1 : DataFrame
        Single summary df from the output of `summarize.summarize`. Will be mean bars of plot.
    summary_df2 : DataFrame
        Single summary df from the output of `summarize.summarize`. Will be percentile lines of plot.
    day_of_week : str
        One of 'mon', 'tue', 'wed', 'thu', 'fri', 'sat, 'sun'
    metric1 : str
        One of 'occupancy', 'arrivals', 'departures' that corresponds to `summary_df1`. Default is 'arrivals'.
    metric2 : str
        One of 'occupancy', 'arrivals', 'departures' that corresponds to `summary_df2`. Default is 'occupancy'.
    plot_style : str, optional
        Matplotlib built in style name. Default is 'ggplot'.
    figsize : Tuple, optional
        Figure size. Default is (15, 10)
    bar_color_mean : str, optional
        Matplotlib color name for the bars representing mean values. Default is 'steelblue'
    alpha: float, optional
        Value between 0 and 1 specifying the opacity of the mean bars. Default is 0.5
    percentiles : list or tuple of floats (e.g. [0.75, 0.95]), optional
        Which percentiles to plot. Default is (0.95)
    pctile_color : list or tuple of color codes (e.g. ['blue', 'green'] or list('gb'), optional
        Line color for each percentile series plotted. Order should match order of percentiles list.
        Default is ('black', 'grey').
    pctile_linestyle : List or tuple of line styles (e.g. ['-', '--']), optional
        Line style for each percentile series plotted. Default is ('-', '--').
    pctile_linewidth : List or tuple of line widths in points (e.g. [1.0, 0.75])
        Line width for each percentile series plotted. Default is (0.75, 0.75).
    bin_size_minutes : int, optional
        Number of minutes in each time bin of the day, default is 60. Use a value that
        divides into 1440 with no remainder
    xlabel : str, optional
        x-axis label, default='Hour'
    ylabel : str, optional
        y-axis label, default='Patients'
    main_title : str, optional
        Main title for plot, default = 'Occupancy by time of day and day of week - {scenario_name}'
    main_title_properties : None or dict, optional
        Dict of `title` properties, default={{'loc': 'left', 'fontsize': 16}}  
    subtitle : str, optional
        title for plot, default = 'All categories'
    subtitle_properties : None or dict, optional
        Dict of `title` properties, default={{'loc': 'left', 'style': 'italic'}}
    legend_properties : None or dict, optional
        Dict of `legend` properties, default={{'loc': 'best', 'frameon': True, 'facecolor': 'w'}}
    scenario_name : str
        Used in output filenames, default is ''
    export_path : str or None, default is None
        If not None, plot is exported to `export_path`
    """

    # Create default titles
    if main_title == '':
        main_title = f'{_metric_name(metric1)} & {_metric_name(metric2).lower()} summary - {_dow_name(day_of_week)}'

    if subtitle == '':
        if len(scenario_name) > 0:
            subtitle = f'Scenario: {scenario_name}'
            main_title += '\n'  # appends newline character to make room for subtitle
    else:
        main_title += '\n'  # appends newline character to make room for subtitle

    with plt.style.context(plot_style):
        # Create empty sized figure
        fig1 = plt.figure(figsize=figsize)
        ax1 = fig1.add_subplot(1, 1, 1)

        num_days = 1

        # Create a list to use as the X-axis values
        num_bins = num_days * 1440 / bin_size_minutes
        base_dates = {'sun': '2015-01-04', 'mon': '2015-01-05', 'tue': '2015-01-06',
                      'wed': '2015-01-07', 'thu': '2015-01-08', 'fri': '2015-01-09', 'sat': '2015-01-10'}
        dow_map = {'sun': 6, 'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5}
        dow_val = dow_map[day_of_week]
        # Adjust the axis labels for first_dow
        base_date_for_first_dow = base_dates[day_of_week]
        timestamps = pd.date_range(base_date_for_first_dow, periods=num_bins, freq=f'{bin_size_minutes}Min').tolist()

        # Adjust the summary df for dow to plot
        arr_summary_df_plot = summary_df1.copy()
        arr_summary_df_plot = arr_summary_df_plot[arr_summary_df_plot['day_of_week'] == dow_val].copy()
        arr_summary_df_plot.sort_values(by=['bin_of_day'], inplace=True)

        # Adjust the summary df for dow to plot
        occ_summary_df_plot = summary_df2.copy()
        occ_summary_df_plot = occ_summary_df_plot[occ_summary_df_plot['day_of_week'] == dow_val].copy()
        occ_summary_df_plot.sort_values(by=['bin_of_day'], inplace=True)

        # Choose appropriate major and minor tick locations
        major_tick_locations = pd.date_range(f'{base_date_for_first_dow} 00:00:00', periods=24, freq='1H').tolist()
        # minor_tick_locations = pd.date_range(f'{base_date_for_first_dow} 01:00:00', periods=24, freq='1H').tolist()

        # Set the tick locations for the axes object
        ax1.set_xticks(major_tick_locations)

        # Add data to the plot
        # Mean occupancy as bars - here's the GOTCHA involving the bar width
        bar_width = 1 / (1440 / bin_size_minutes)
        ax1.bar(timestamps, arr_summary_df_plot['mean'], label=f'Mean {metric1}',
                width=bar_width, color=bar_color_mean, edgecolor=None, alpha=alpha)

        # Percentiles as lines
        # Style the line for the occupancy percentile
        cycler_pctiles = (
                cycler(color=pctile_color) + cycler(linestyle=pctile_linestyle) + cycler(linewidth=pctile_linewidth))
        ax1.set_prop_cycle(cycler_pctiles)

        for p in percentiles:
            pct_name = pctile_field_name(p)
            label = f'{pct_name[1:]}th %ile {metric2}'
            ax1.plot(timestamps, occ_summary_df_plot[pct_name], label=label)
            
        # Create formatter variables
        # day_fmt = '' if num_days == 1 else '%a'
        # dayofweek_formatter = DateFormatter(day_fmt)
        hour_formatter = DateFormatter('%H')

        # Format the tick labels
        ax1.xaxis.set_major_formatter(hour_formatter)

        # Slide the major tick labels underneath the default location by 20 points
        # ax1.tick_params(which='major', pad=20)

        # Add other chart elements

        # Set plot and axis titles
        # Be nice to have application and session level defaults - style sheets for app level?
        if main_title_properties is None:
            main_title_properties = {}

        # Create an invisible subplot to add the second title
        ax2 = fig1.add_axes(ax1.get_position(), zorder=1, frame_on=False)
        ax2.set_axis_off()
        ax2.set_title(main_title, **main_title_properties)

        if subtitle_properties is None:
            subtitle_properties = {}
        ax1.set_title(subtitle, **subtitle_properties)

        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)

        # Legend
        if legend_properties is None:
            legend_properties = {}
        ax1.legend(**legend_properties)

        # save figure
        if export_path is not None:
            week_range_str = day_of_week
            plot_png = f'{scenario_name}_{metric1}_{metric2}_{week_range_str}.png'
            png_wpath = Path(export_path, plot_png)
            plt.savefig(png_wpath, bbox_inches='tight')

        # Suppress plot output in notebook
        plt.close()

    return fig1
