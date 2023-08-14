"""Hillmaker"""

# Copyright 2022-2023 Mark Isken, Jacob Norman


from pathlib import Path
# f rom argparse import ArgumentParser, Namespace, SUPPRESS
import logging
# from datetime import datetime
from typing import Dict, Optional

import pandas as pd

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from hillmaker.bydatetime import make_bydatetime
from hillmaker.summarize import summarize
from hillmaker.hmlib import HillTimer
from hillmaker.plotting import make_hill_plot


def setup_logger(verbosity: int):
    # Set logging level
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Needed to prevent dup messages when module imported
    logger_handler = logging.StreamHandler()
    logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_handler.setFormatter(logger_formatter)

    if verbosity == 0:
        root_logger.setLevel(logging.WARNING)
        logger_handler.setLevel(logging.WARNING)
    elif verbosity == 1:
        root_logger.setLevel(logging.INFO)
        logger_handler.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.DEBUG)
        logger_handler.setLevel(logging.DEBUG)

    root_logger.addHandler(logger_handler)


def make_hills(scenario_name=None,
               stops_df=None,
               in_field=None, out_field=None,
               start_analysis_dt=None, end_analysis_dt=None,
               cat_field=None,
               bin_size_minutes=60,
               percentiles=(0.25, 0.5, 0.75, 0.95, 0.99),
               cats_to_exclude=None,
               occ_weight_field=None,
               cap=None,
               nonstationary_stats=True,
               stationary_stats=True,
               export_bydatetime_csv=True,
               export_summaries_csv=True,
               make_dow_plot=True,
               make_week_plot=True,
               export_dow_plot=False,
               export_week_plot=False,
               xlabel=None,
               ylabel=None,
               output_path=Path('.'),
               edge_bins=1,
               verbosity=0):
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
    cat_field : str, optional
        Column name corresponding to the categories. If none is specified, then only overall occupancy is summarized.
        Default is None
    bin_size_minutes : int, optional
        Number of minutes in each time bin of the day, default is 60. Use a value that
        divides into 1440 with no remainder
    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)
    cats_to_exclude : list, optional
        Category values to ignore, default is None
    occ_weight_field : str, optional
        Column name corresponding to the weights to use for occupancy incrementing, default is None
        which corresponds to a weight of 1.0.
    edge_bins: int, default 1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=whole bin
    cap : int, optional
        Capacity of area being analyzed, default is None
    nonstationary_stats : bool, optional
       If True, datetime bin stats are computed. Else, they aren't computed. Default is True
    stationary_stats : bool, optional
       If True, overall, non time bin dependent, stats are computed. Else, they aren't computed. Default is True
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
        y-axis label, default='Patients'
    output_path : str or Path, optional
        Destination path for exported csv and png files, default is current directory
    verbosity : int, optional
        Used to set level in loggers. 0=logging.WARNING (default=0), 1=logging.INFO, 2=logging.DEBUG

    Returns
    -------
    dict of DataFrames
       The bydatetime DataFrames and all summary DataFrames.
    """

    setup_logger(verbosity)

    # This should inherit level from root logger
    logger = logging.getLogger(__name__)

    # Create pandas Timestamps for start and end of the analysis span
    try:
        start_analysis_dt_ts = pd.Timestamp(start_analysis_dt)
    except ValueError as error:
        raise ValueError(f'Cannot convert {start_analysis_dt} to Timestamp\n{error}')

    try:
        end_analysis_dt_ts = pd.Timestamp(end_analysis_dt).floor("d") + pd.Timedelta(86399, "s")
    except ValueError as error:
        raise ValueError(f'Cannot convert {end_analysis_dt} to Timestamp\n{error}')

    # numpy datetime64 versions of analysis span end points
    start_analysis_dt_np = start_analysis_dt_ts.to_datetime64()
    end_analysis_dt_np = end_analysis_dt_ts.to_datetime64()
    if start_analysis_dt_np > end_analysis_dt_np:
        raise ValueError(f'end date {end_analysis_dt_np} is before start date {start_analysis_dt_np}')

    # Looking for missing entry and departure timestamps
    num_recs_missing_entry_ts = stops_df[in_field].isna().sum()
    num_recs_missing_exit_ts = stops_df[out_field].isna().sum()
    if num_recs_missing_entry_ts > 0:
        logger.warning(f'{num_recs_missing_entry_ts} records with missing entry timestamps - records ignored')
    if num_recs_missing_exit_ts > 0:
        logger.warning(f'{num_recs_missing_exit_ts} records with missing exit timestamps - records ignored')

    # Create mutable copy of stops_df containing only necessary fields
    stops_working_df = pd.DataFrame(stops_df[in_field], stops_df[out_field])
    if cat_field is not None:
        stops_working_df[cat_field] = stops_df[cat_field]

    # Filter out records that don't overlap the analysis span or have missing entry and/or exit timestamps
    stops_working_df = stops_working_df.loc[(stops_working_df[in_field] < end_analysis_dt_ts) &
                                            (~stops_working_df[stops_working_df[in_field]].isna()) &
                                            (~stops_working_df[stops_working_df[out_field]].isna()) &
                                            (stops_working_df[out_field] >= start_analysis_dt_ts)]

    # reset index of df to ensure sequential numbering
    stops_working_df = stops_working_df.reset_index(drop=True)

    # Create the bydatetime DataFrame
    with HillTimer() as t:
        starttime = t.start
        bydt_dfs = make_bydatetime(stops_working_df,
                                   in_field,
                                   out_field,
                                   start_analysis_dt,
                                   end_analysis_dt,
                                   cat_field,
                                   bin_size_minutes,
                                   cat_to_exclude=cats_to_exclude,
                                   occ_weight_field=occ_weight_field,
                                   edge_bins=edge_bins)

    logger.info(f"Datetime matrix created (seconds): {t.interval:.4f}")

    # Create the summary stats DataFrames
    summary_dfs = {}
    if nonstationary_stats or stationary_stats:
        with HillTimer() as t:
            summary_dfs = summarize(bydt_dfs,
                                    nonstationary_stats=nonstationary_stats,
                                    stationary_stats=stationary_stats,
                                    percentiles=percentiles,
                                    verbosity=verbosity)

        logger.info(f"Summaries by datetime created (seconds): {t.interval:.4f}")

    # Export results to csv if requested
    if export_bydatetime_csv:
        with HillTimer() as t:
            export_bydatetime(bydt_dfs, scenario_name, output_path)

        logger.info(f"By datetime exported to csv in {output_path} (seconds): {t.interval:.4f}")

    if export_summaries_csv:
        with HillTimer() as t:
            if nonstationary_stats:
                export_summaries(summary_dfs, scenario_name, output_path, 'nonstationary')
            if stationary_stats:
                export_summaries(summary_dfs, scenario_name, output_path, 'stationary')

        logger.info(f"Summaries exported to csv in {output_path} (seconds): {t.interval:.4f}")

    # Create and export full week plots if requested
    plots = {}
    if make_week_plot:
        with HillTimer() as t:
            for metric in summary_dfs['nonstationary']['dow_binofday']:
                fullwk_df = summary_dfs['nonstationary']['dow_binofday'][metric]
                fullwk_df = fullwk_df.reset_index()

                week_range_str = 'week'
                plot_key = f'{scenario_name}_{metric}_plot_{week_range_str}'

                plot = make_hill_plot(fullwk_df, scenario_name, metric, export_path=output_path,
                                      bin_size_minutes=bin_size_minutes, cap=cap,
                                      xlabel=xlabel, ylabel=ylabel,
                                      export_png=export_week_plot)
                plots[plot_key] = plot

        logger.info(f"Full week plots created (seconds): {t.interval:.4f}")

    # Create and export individual day of week plots if requested
    if make_dow_plot:
        with HillTimer() as t:
            for metric in summary_dfs['nonstationary']['dow_binofday']:
                fullwk_df = summary_dfs['nonstationary']['dow_binofday'][metric]
                fullwk_df = fullwk_df.reset_index()
                for dow in fullwk_df['dow_name'].unique():
                    dow_df = fullwk_df.loc[fullwk_df['dow_name'] == dow]
                    week_range_str = dow
                    plot_key = f'{scenario_name}_{metric}_plot_{week_range_str}'
                    plot = make_hill_plot(dow_df, scenario_name, metric, export_path=output_path,
                                          bin_size_minutes=bin_size_minutes, cap=cap, week_range=dow,
                                          xlabel=xlabel,
                                          ylabel=ylabel, export_png=export_dow_plot)
                    plots[plot_key] = plot

        logger.info(f"Individual day of week plots created (seconds): {t.interval:.4f}")

    if len(plots) > 0:
        hills = {'bydatetime': bydt_dfs, 'summaries': summary_dfs, 'plots': plots}
    else:
        hills = {'bydatetime': bydt_dfs, 'summaries': summary_dfs}

    # All done
    endtime = t.end
    logger.info(f"Total time (seconds): {endtime - starttime:.4f}")

    return hills


def export_bydatetime(bydt_dfs, scenario_name, export_path):
    """
    Export bydatetime DataFrames to csv files.


    Parameters
    ----------
    bydt_dfs: dict of DataFrames
        Output from make_hills to be exported

    scenario_name: str
        Used in output filenames

    export_path: str or Path
        Destination path for exported csv files
    """

    for d in bydt_dfs:
        file_bydt_csv = f'{scenario_name}_bydatetime_{d}.csv'
        Path(export_path).mkdir(parents=True, exist_ok=True)
        csv_wpath = Path(export_path, file_bydt_csv)

        dt_cols = ['arrivals', 'departures', 'occupancy',
                   'dow_name', 'bin_of_day_str', 'day_of_week', 'bin_of_day', 'bin_of_week']

        bydt_dfs[d].to_csv(csv_wpath, index=True, float_format='%.6f', columns=dt_cols)


def export_summaries(summary_all_dfs, scenario_name, export_path, temporal_key):
    """
    Export occupancy, arrival, and departure summary DataFrames to csv files.


    Parameters
    ----------
    summary_all_dfs: dict of DataFrames
        Output from make_hills to be exported

    scenario_name: str
        Used in output filenames

    export_path: str
        Destination path for exported csv files

    temporal_key: str
        'nonstationary' or 'stationary'

    """

    summary_dfs = summary_all_dfs[temporal_key]
    for d in summary_dfs:
        df_dict = summary_dfs[d]
        for metric in ['occupancy', 'arrivals', 'departures']:

            df = df_dict[metric]
            file_summary_csv = scenario_name + '_' + metric
            if len(d) > 0:
                file_summary_csv = file_summary_csv + '_' + d + '.csv'
            else:
                file_summary_csv = file_summary_csv + '.csv'

            Path(export_path).mkdir(parents=True, exist_ok=True)
            csv_wpath = Path(export_path, file_summary_csv)

            catfield = df.index.names

            if temporal_key == 'nonstationary' or catfield[0] is not None:
                df.to_csv(csv_wpath, index=True, float_format='%.6f')
            else:
                df.to_csv(csv_wpath, index=False, float_format='%.6f')


