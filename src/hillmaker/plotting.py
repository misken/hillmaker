# Copyright 2022-2023 Mark Isken, Jacob Norman
import logging
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from pathlib import Path

# from hillmaker.scenario import Scenario
from hillmaker.hmlib import HillTimer


def make_week_dow_plots(scenario: 'Scenario', hills: dict):
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
    if scenario.make_all_week_plots:
        with HillTimer() as t:
            for metric in hills['summaries']['nonstationary']['dow_binofday']:
                fullwk_df = hills['summaries']['nonstationary']['dow_binofday'][metric]
                fullwk_df = fullwk_df.reset_index()

                week_range_str = 'week'
                plot_key = f'{scenario.scenario_name}_{metric}_plot_{week_range_str}'

                plot = make_hill_plot(fullwk_df, scenario.scenario_name, metric, export_path=scenario.output_path,
                                      bin_size_minutes=scenario.bin_size_minutes, cap=scenario.cap,
                                      xlabel=scenario.xlabel, ylabel=scenario.ylabel,
                                      export_png=scenario.export_all_week_plots)
                plots[plot_key] = plot

        logger.info(f"Full week plots created (seconds): {t.interval:.4f}")

    # Create and export individual day of week plots if requested
    if scenario.make_all_dow_plots:
        with HillTimer() as t:
            for metric in hills['summaries']['nonstationary']['dow_binofday']:
                fullwk_df = hills['summaries']['nonstationary']['dow_binofday'][metric]
                fullwk_df = fullwk_df.reset_index()
                for dow in fullwk_df['dow_name'].unique():
                    dow_df = fullwk_df.loc[fullwk_df['dow_name'] == dow]
                    week_range_str = dow
                    plot_key = f'{scenario.scenario_name}_{metric}_plot_{week_range_str}'
                    plot = make_hill_plot(dow_df, scenario.scenario_name, metric, export_path=scenario.output_path,
                                          bin_size_minutes=scenario.bin_size_minutes, cap=scenario.cap, week_range=dow,
                                          xlabel=scenario.xlabel, ylabel=scenario.ylabel,
                                          export_png=scenario.export_all_dow_plots)
                    plots[plot_key] = plot

        logger.info(f"Individual day of week plots created (seconds): {t.interval:.4f}")

    return plots


def make_hill_plot(summary_df: pd.DataFrame, scenario_name: str, metric: str,
                   export_path: Path | str = Path('.'),
                   bin_size_minutes: int = 60, cap: int = None,
                   week_range: str = 'week',
                   xlabel: str = 'Hour', ylabel: str = 'Patients',
                   export_png: bool = False):
    """
    Makes and optionally exports day of week plot

    Takes output DataFrames of `summarize.summarize` and plots mean and percentile
    values for occupancy, arrival, and departure categories. Designed to be run in
    a loop in order to isolate plot to a single day of week.

    Parameters
    ----------
    summary_df : DataFrame
        Single summary df from the output of `summarize.summarize`
    scenario_name : str
        Used in output filenames
    metric : str
        Name of make_hills summary df being plotted
    export_path : str or Path, optional
        Destination path for exported png files, default is current directory
    bin_size_minutes : int, optional
        Number of minutes in each time bin of the day, default is 60. Use a value that
        divides into 1440 with no remainder
    cap : int, optional
        Capacity of area being analyzed, default is None
    week_range : str
        Week range of summary df. Default is 'week', can also take the form of
        the first three characters of a day of week name (ex: 'tue')
    xlabel : str
        x-axis label, default='Hour'
    ylabel : str
        y-axis label, default='Patients'
    export_png : bool, default is False
        If True, plot is exported to png file to `export_path`
    """

    plt.style.use('seaborn-darkgrid')
    fig1 = plt.figure(figsize=(15, 10))
    ax1 = fig1.add_subplot(1, 1, 1)

    # infer number of days being plotted
    num_days = len(summary_df) / (60 / bin_size_minutes * 24)

    # Create a list to use as the X-axis values
    num_bins = num_days * 1440 / bin_size_minutes
    # TODO: This is a Monday. Make flexible so any dow can be "first".
    base_date_for_first_dow = '2015-01-05'
    timestamps = pd.date_range(base_date_for_first_dow, periods=num_bins, freq=f'{bin_size_minutes}Min').tolist()

    # Choose appropriate major and minor tick locations
    major_tick_locations = pd.date_range(f'{base_date_for_first_dow} 12:00:00', periods=7, freq='24H').tolist()
    minor_tick_locations = pd.date_range(f'{base_date_for_first_dow} 06:00:00', periods=42, freq='4H').tolist()

    # Set the tick locations for the axes object
    ax1.set_xticks(major_tick_locations)
    ax1.set_xticks(minor_tick_locations, minor=True)

    # Specify the mean occupancy and percentile values. TODO - let user choose series to plot
    mean_occ = summary_df['mean']
    pctile_occ = summary_df['p95']

    # Styling of bars, lines, plot area
    # Style the bars for mean occupancy
    bar_color = 'steelblue'

    # Style the line for the occupancy percentile
    pctile_line_style = '-'
    pctile_color = 'grey'

    # Add data to the plot
    # Mean occupancy as bars - here's the GOTCHA involving the bar width
    bar_width = 1 / (1440 / bin_size_minutes)
    ax1.bar(timestamps, mean_occ, label=f'Mean {metric}', width=bar_width, color=bar_color)

    # Some percentile as a line
    ax1.plot(timestamps, pctile_occ, linestyle=pctile_line_style, label=f'95th %ile {metric}', color=pctile_color)

    # establish capacity horizontal line if supplied
    if cap is not None and metric == 'occupancy':
        plt.axhline(cap, color='r', linestyle='--', label='Capacity')

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
    sup_title = fig1.suptitle(f'{metric.title()} by Time of Day - {week_range.title()}\n{scenario_name.title()}',
                              x=0.125, y=0.95, horizontalalignment='left', verticalalignment='top', fontsize=16)

    ax1.set_title('All category types', loc='left', style='italic')
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel)

    # Legend
    ax1.legend(loc='best', frameon=True, facecolor='w')

    # save figure
    if export_png:
        week_range_str = week_range.lower().replace(' ', '_')
        plot_png = f'{scenario_name}_{metric}_plot_{week_range_str}.png'
        png_wpath = Path(export_path, plot_png)
        plt.savefig(png_wpath, bbox_extra_artists=[sup_title], bbox_inches='tight')

    # Suppress plot output in notebook
    plt.close()

    return fig1


def make_week_hill_plot(summary_df: pd.DataFrame, scenario_name: str, metric: str,

                        bin_size_minutes: int = 60,
                        cap: int = None,
                        first_dow: str = 'Mon',
                        xlabel: str = 'Hour',
                        ylabel: str = 'Patients',
                        export_path: Path | str | None = None,):
    """
    Makes and optionally exports week plot for occupancy, arrivals, or departures.

    Takes output DataFrames of `summarize.summarize` and plots mean and percentile
    values for occupancy, arrival, and departure categories.

    Parameters
    ----------
    summary_df : DataFrame
        Single summary df from the output of `summarize.summarize`
    scenario_name : str
        Used in output filenames
    metric : str
        Name of make_hills summary df being plotted
    export_path : str or Path, optional
        Destination path for exported png files, default is current directory
    bin_size_minutes : int, optional
        Number of minutes in each time bin of the day, default is 60. Use a value that
        divides into 1440 with no remainder
    cap : int, optional
        Capacity of area being analyzed, default is None
    week_range : str
        Week range of summary df. Default is 'week', can also take the form of
        the first three characters of a day of week name (ex: 'tue')
    xlabel : str
        x-axis label, default='Hour'
    ylabel : str
        y-axis label, default='Patients'
    export_png : bool, default is False
        If True, plot is exported to png file to `export_path`
    """

    plt.style.use('seaborn-darkgrid')
    fig1 = plt.figure(figsize=(15, 10))
    ax1 = fig1.add_subplot(1, 1, 1)

    # infer number of days being plotted
    num_days = len(summary_df) / (60 / bin_size_minutes * 24)

    # Create a list to use as the X-axis values
    num_bins = num_days * 1440 / bin_size_minutes
    # TODO: This is a Monday. Make flexible so any dow can be "first".
    base_date_for_first_dow = '2015-01-05'
    timestamps = pd.date_range(base_date_for_first_dow, periods=num_bins, freq=f'{bin_size_minutes}Min').tolist()

    # Choose appropriate major and minor tick locations
    major_tick_locations = pd.date_range(f'{base_date_for_first_dow} 12:00:00', periods=7, freq='24H').tolist()
    minor_tick_locations = pd.date_range(f'{base_date_for_first_dow} 06:00:00', periods=42, freq='4H').tolist()

    # Set the tick locations for the axes object
    ax1.set_xticks(major_tick_locations)
    ax1.set_xticks(minor_tick_locations, minor=True)

    # Specify the mean occupancy and percentile values. TODO - let user choose series to plot
    mean_occ = summary_df['mean']
    pctile_occ = summary_df['p95']

    # Styling of bars, lines, plot area
    # Style the bars for mean occupancy
    bar_color = 'steelblue'

    # Style the line for the occupancy percentile
    pctile_line_style = '-'
    pctile_color = 'grey'

    # Add data to the plot
    # Mean occupancy as bars - here's the GOTCHA involving the bar width
    bar_width = 1 / (1440 / bin_size_minutes)
    ax1.bar(timestamps, mean_occ, label=f'Mean {metric}', width=bar_width, color=bar_color)

    # Some percentile as a line
    ax1.plot(timestamps, pctile_occ, linestyle=pctile_line_style, label=f'95th %ile {metric}', color=pctile_color)

    # establish capacity horizontal line if supplied
    if cap is not None and metric == 'occupancy':
        plt.axhline(cap, color='r', linestyle='--', label='Capacity')

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
    sup_title = fig1.suptitle(f'{metric.title()} by Time of Day - {week_range.title()}\n{scenario_name.title()}',
                              x=0.125, y=0.95, horizontalalignment='left', verticalalignment='top', fontsize=16)

    ax1.set_title('All category types', loc='left', style='italic')
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel)

    # Legend
    ax1.legend(loc='best', frameon=True, facecolor='w')

    # save figure
    if export_png:
        week_range_str = week_range.lower().replace(' ', '_')
        plot_png = f'{scenario_name}_{metric}_plot_{week_range_str}.png'
        png_wpath = Path(export_path, plot_png)
        plt.savefig(png_wpath, bbox_extra_artists=[sup_title], bbox_inches='tight')

    # Suppress plot output in notebook
    plt.close()

    return fig1
