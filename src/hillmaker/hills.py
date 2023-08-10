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

from hillmaker.parameters import Parameters
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





def make_hills(scenario: Parameters) -> Dict:
    """
    Compute occupancy, arrival, and departure statistics by category,
    time bin of day and day of week.

    Main function that first calls `bydatetime.make_bydatetime` to calculate occupancy, arrival
    and departure values by date by time bin and then calls `summarize.summarize`
    to compute the summary statistics.


    Returns
    -------
    dict of DataFrames
       The bydatetime DataFrames and all summary DataFrames.
    """

    setup_logger(scenario.verbosity)

    # This should inherit level from root logger
    logger = logging.getLogger(__name__)

    # Leaving these input validation checks in for now, even though
    # the pydantic model takes care of them
    # Check if in and out fields are part of stops_df
    scenario = prep_scenario(scenario, logger)

    # if scenario.in_field not in list(scenario.stops_df):
    #     raise ValueError(f'Bad in_field - {scenario.in_field} is not part of the stops dataframe')
    #
    # if scenario.out_field not in list(scenario.stops_df):
    #     raise ValueError(f'Bad out_field - {scenario.out_field} is not part of the stops dataframe')
    #
    # # Check if catfield is part of stops_df
    # if scenario.cat_field is not None:
    #     if scenario.cat_field not in list(scenario.stops_df):
    #         raise ValueError(f'Bad cat_field - {scenario.cat_field} is not part of the stops dataframe')

    # pandas Timestamp versions of analysis span end points
    # The pydantic model does NOT do these timestamp validations
    # try:
    #     start_analysis_dt_ts = pd.Timestamp(scenario.start_analysis_dt)
    # except ValueError as error:
    #     raise ValueError(f'Cannot convert {scenario.start_analysis_dt} to Timestamp\n{error}')
    #
    # try:
    #     end_analysis_dt_ts = pd.Timestamp(scenario.end_analysis_dt).floor("d") + pd.Timedelta(86399, "s")
    # except ValueError as error:
    #     raise ValueError(f'Cannot convert {scenario.end_analysis_dt} to Timestamp\n{error}')
    #
    # # numpy datetime64 versions of analysis span end points
    # start_analysis_dt_np = start_analysis_dt_ts.to_datetime64()
    # end_analysis_dt_np = end_analysis_dt_ts.to_datetime64()
    # if start_analysis_dt_np > end_analysis_dt_np:
    #     raise ValueError(f'end date {end_analysis_dt_np} is before start date {start_analysis_dt_np}')

    # # Looking for missing entry and departure timestamps
    # num_recs_missing_entry_ts = scenario.stops_df[scenario.in_field].isna().sum()
    # num_recs_missing_exit_ts = scenario.stops_df[scenario.out_field].isna().sum()
    # if num_recs_missing_entry_ts > 0:
    #     logger.warning(f'{num_recs_missing_entry_ts} records with missing entry timestamps - records ignored')

    # # Update departure timestamp for missing values if no_censored_departures=False
    # if not scenario.adjust_censored_departures:
    #     # num_recs_uncensored = num_recs_missing_exit_ts
    #     if num_recs_missing_exit_ts > 0:
    #         msg = 'records with missing exit timestamps - end of analysis range used for occupancy purposes'
    #         logger.info(
    #             f'{num_recs_missing_exit_ts} {msg}')
    #         uncensored_out_field = f'{scenario.out_field}_uncensored'
    #         uncensored_out_value = pd.Timestamp(scenario.end_analysis_dt).floor("d") + pd.Timedelta(1, "d")
    #         scenario.stops_df[uncensored_out_field] = scenario.stops_df[scenario.out_field].fillna(
    #             value=uncensored_out_value)
    #         active_out_field = uncensored_out_field
    #     else:
    #         # Records with missing departures will be ignored
    #         active_out_field = scenario.out_field
    #         if num_recs_missing_exit_ts > 0:
    #             logger.warning(f'{num_recs_missing_exit_ts} records with missing exit timestamps - records ignored')
    # else:
    #     active_out_field = scenario.out_field

    # # Filter out records that don't overlap the analysis span or have missing entry timestamps
    # scenario.stops_df = scenario.stops_df.loc[(scenario.stops_df[scenario.in_field] < end_analysis_dt_ts) &
    #                                           (~scenario.stops_df[scenario.in_field].isna()) &
    #                                           (scenario.stops_df[active_out_field] >= start_analysis_dt_ts)]

    # # reset index of df to ensure sequential numbering
    # stops_df = scenario.stops_df.reset_index(drop=True)

    # Create the bydatetime DataFrame
    with HillTimer() as t:
        starttime = t.start
        bydt_dfs = make_bydatetime(scenario.stops_df,
                                   scenario.in_field,
                                   active_out_field,
                                   scenario.start_analysis_dt,
                                   scenario.end_analysis_dt,
                                   scenario.cat_field,
                                   scenario.bin_size_minutes,
                                   cat_to_exclude=scenario.cats_to_exclude,
                                   occ_weight_field=scenario.occ_weight_field,
                                   edge_bins=scenario.edge_bins)

    logger.info(f"Datetime matrix created (seconds): {t.interval:.4f}")

    # Create the summary stats DataFrames
    summary_dfs = {}
    if scenario.nonstationary_stats or scenario.stationary_stats:
        with HillTimer() as t:
            summary_dfs = summarize(bydt_dfs,
                                    nonstationary_stats=scenario.nonstationary_stats,
                                    stationary_stats=scenario.stationary_stats,
                                    percentiles=scenario.percentiles,
                                    verbosity=scenario.verbosity)

        logger.info(f"Summaries by datetime created (seconds): {t.interval:.4f}")

    # Export results to csv if requested
    if scenario.export_bydatetime_csv:
        with HillTimer() as t:
            export_bydatetime(bydt_dfs, scenario.scenario_name, scenario.output_path)

        logger.info(f"By datetime exported to csv in {scenario.output_path} (seconds): {t.interval:.4f}")

    if scenario.export_summaries_csv:
        with HillTimer() as t:
            if scenario.nonstationary_stats:
                export_summaries(summary_dfs, scenario.scenario_name, scenario.output_path, 'nonstationary')
            if scenario.stationary_stats:
                export_summaries(summary_dfs, scenario.scenario_name, scenario.output_path, 'stationary')

        logger.info(f"Summaries exported to csv in {scenario.output_path} (seconds): {t.interval:.4f}")

    # Create and export full week plots if requested
    plots = {}
    if scenario.make_week_plot:
        with HillTimer() as t:
            for metric in summary_dfs['nonstationary']['dow_binofday']:
                fullwk_df = summary_dfs['nonstationary']['dow_binofday'][metric]
                fullwk_df = fullwk_df.reset_index()

                week_range_str = 'week'
                plot_key = f'{scenario.scenario_name}_{metric}_plot_{week_range_str}'

                plot = make_hill_plot(fullwk_df, scenario.scenario_name, metric, export_path=scenario.output_path,
                                      bin_size_minutes=scenario.bin_size_minutes, cap=scenario.cap,
                                      xlabel=scenario.xlabel, ylabel=scenario.ylabel,
                                      export_png=scenario.export_week_png)
                plots[plot_key] = plot

        logger.info(f"Full week plots created (seconds): {t.interval:.4f}")

    # Create and export individual day of week plots if requested
    if scenario.make_dow_plot:
        with HillTimer() as t:
            for metric in summary_dfs['nonstationary']['dow_binofday']:
                fullwk_df = summary_dfs['nonstationary']['dow_binofday'][metric]
                fullwk_df = fullwk_df.reset_index()
                for dow in fullwk_df['dow_name'].unique():
                    dow_df = fullwk_df.loc[fullwk_df['dow_name'] == dow]
                    week_range_str = dow
                    plot_key = f'{scenario.scenario_name}_{metric}_plot_{week_range_str}'
                    plot = make_hill_plot(dow_df, scenario.scenario_name, metric, export_path=scenario.output_path,
                                          bin_size_minutes=scenario.bin_size_minutes, cap=scenario.cap, week_range=dow,
                                          xlabel=scenario.xlabel,
                                          ylabel=scenario.ylabel, export_png=scenario.export_dow_png)
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

# def update_params(params, toml_config):
#     """
#     Update args namespace values from toml_config dictionary
#
#     Parameters
#     ----------
#     params : namespace
#     toml_config : dict from loading TOML config file
#
#     Returns
#     -------
#     Updated parameters namespace
#     """
#
#     # Convert pydantic model to a dict
#     params_dict = params.dict()
#
#     # Flatten toml config (we know there are no key clashes and only one nesting level)
#     # Update args dict from config dict
#     for outer_key, outer_val in toml_config.items():
#         for key, val in outer_val.items():
#             params_dict[key] = val
#
#     # Convert dict to updated pydantic model
#     params = Hills.parse_obj(params_dict)
#     return params
