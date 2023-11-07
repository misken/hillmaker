"""Hillmaker"""

# Copyright 2022-2023 Mark Isken, Jacob Norman

from pathlib import Path
import logging

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from hillmaker.bydatetime import make_bydatetime
from hillmaker.summarize import summarize, summarize_los
from hillmaker.hmlib import HillTimer
from hillmaker.plotting import make_plots


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


def compute_hills_stats(scenario):
    """
    Compute occupancy, arrival, and departure statistics by category, time bin of day and day of week.

    Main function that first calls `bydatetime.make_bydatetime` to calculate occupancy, arrival
    and departure values by date by time bin and then calls `summarize.summarize`
    to compute the summary statistics.

    Parameters
    ----------
    scenario : Scenario

    Returns
    -------
    dict of DataFrames
       The bydatetime DataFrames and all summary DataFrames.
    """

    # Logging
    setup_logger(scenario.verbosity)
    # This should inherit level from root logger
    logger = logging.getLogger(__name__)

    # Create the bydatetime DataFrame
    with HillTimer() as t:
        bydt_dfs, bydt_highres_dfs = make_bydatetime(scenario.stops_preprocessed_df,
                                                     scenario.in_field,
                                                     scenario.out_field,
                                                     scenario.start_analysis_dt,
                                                     scenario.end_analysis_dt,
                                                     cat_field=scenario.cat_field,
                                                     bin_size_minutes=scenario.bin_size_minutes,
                                                     highres_bin_size_minutes=scenario.highres_bin_size_minutes,
                                                     keep_highres_bydatetime=scenario.keep_highres_bydatetime,
                                                     cat_to_exclude=scenario.cats_to_exclude,
                                                     occ_weight_field=scenario.occ_weight_field,
                                                     edge_bins=scenario.edge_bins)

    logger.debug(f"Datetime matrix created (seconds): {t.interval:.4f}")

    # Create the summary stats DataFrames
    summary_dfs = {}
    if scenario.nonstationary_stats or scenario.stationary_stats:
        with HillTimer() as t:
            summary_dfs = summarize(bydt_dfs,
                                    nonstationary_stats=scenario.nonstationary_stats,
                                    stationary_stats=scenario.stationary_stats,
                                    percentiles=scenario.percentiles,
                                    verbosity=scenario.verbosity)

        logger.debug(f"Summaries by datetime created (seconds): {t.interval:.4f}")

    # Compute los summary
    with HillTimer() as t:
        los_summary = summarize_los(scenario.stops_preprocessed_df,
                                    scenario.los_field_name,
                                    cat_field=scenario.cat_field)

    logger.debug(f"Length of stay summary created (seconds): {t.interval:.4f}")

    # Gather results
    hills = {'bydatetime': bydt_dfs, 'summaries': summary_dfs, 'los_summary': los_summary,
             'settings': {'scenario_name': scenario.scenario_name,
                          'in_field': scenario.in_field,
                          'out_field': scenario.out_field,
                          'start_analysis_dt': scenario.start_analysis_dt,
                          'end_analysis_dt': scenario.start_analysis_dt,
                          'cat_field': scenario.cat_field,
                          'occ_weight_field': scenario.occ_weight_field,
                          'bin_size_minutes': scenario.bin_size_minutes,
                          'los_units': scenario.los_units,
                          'edge_bins': scenario.edge_bins,
                          'highres_bin_size_minutes': scenario.highres_bin_size_minutes}}

    if scenario.keep_highres_bydatetime:
        hills['bydatetime_highres'] = bydt_highres_dfs

    return hills


def _make_hills(scenario):
    """
    Compute occupancy, arrival, and departure statistics by category, time bin of day and day of week.

    Main function that first calls `bydatetime.make_bydatetime` to calculate occupancy, arrival
    and departure values by date by time bin and then calls `summarize.summarize`
    to compute the summary statistics.

    Parameters
    ----------

    scenario : Scenario


    Returns
    -------
    dict of DataFrames and plots
       The bydatetime DataFrames, all summary DataFrames and any plots created.
    """

    # Logging
    setup_logger(scenario.verbosity)
    # This should inherit level from root logger
    logger = logging.getLogger(__name__)

    # Compute stats
    with HillTimer() as t:
        starttime = t.start
        logger.info(f"Starting scenario {scenario.scenario_name}")
        hills = compute_hills_stats(scenario)

    logger.info(f"bydatetime and summaries by datetime created (seconds): {t.interval:.4f}")

    # Export results to csv if requested
    if scenario.export_bydatetime_csv:
        with HillTimer() as t:
            export_bydatetime(hills['bydatetime'], scenario.scenario_name, scenario.csv_export_path)

        logger.info(f"By datetime exported to csv in {scenario.csv_export_path} (seconds): {t.interval:.4f}")

    if scenario.export_summaries_csv:
        with HillTimer() as t:
            if scenario.nonstationary_stats:
                export_summaries(hills['summaries'], scenario.scenario_name, scenario.csv_export_path, 'nonstationary')
            if scenario.stationary_stats:
                export_summaries(hills['summaries'], scenario.scenario_name, scenario.csv_export_path, 'stationary')

        logger.info(f"Summaries exported to csv in {scenario.csv_export_path} (seconds): {t.interval:.4f}")

    # Plots
    if scenario.make_all_week_plots or scenario.make_all_dow_plots or \
            scenario.export_all_week_plots or scenario.export_all_dow_plots:
        with HillTimer() as t:
            plots = make_plots(scenario, hills)
            hills['plots'] = plots

    # All done
    endtime = t.end
    runtime = endtime - starttime
    hills['runtime'] = runtime

    logger.info(f"Total time (seconds): {endtime - starttime:.4f}")
    logger.debug(f"Scenario {scenario.scenario_name} complete at {endtime}\n")

    return hills


def get_plot(hills: dict, flow_metric: str = 'occupancy', day_of_week: str = 'week'):
    """
    Get plot object for specified flow metric and whether full week or specified day of week.

    Parameters
    ----------
    hills : dict
        Created by `make_hills`
    flow_metric : str
        Either of 'arrivals', 'departures', 'occupancy' ('a', 'd', and 'o' are sufficient).
        Default='occupancy'
    day_of_week : str
        Either of 'week', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'. Default='week'

    Returns
    -------
    plot object from matplotlib

    """
    try:
        if 'plots' not in hills.keys():
            raise KeyError
    except KeyError:
        print(f'No plots exist.')
        return None

    scenario_name = hills['settings']['scenario_name']

    flow_metrics = {'a': 'arrivals', 'd': 'departures', 'o': 'occupancy'}
    flow_metric_str = flow_metrics[flow_metric[0].lower()]

    if day_of_week.lower() != 'week':
        day_of_week_str = day_of_week[:3]
    else:
        day_of_week_str = 'week'

    plot_name = f'{scenario_name}_{flow_metric_str}_plot_{day_of_week_str}'
    try:
        plot = hills['plots'][plot_name]
        return plot
    except KeyError as error:
        print(f'The plot {error} does not exist.')
        return None


def get_summary_df(hills: dict, flow_metric: str = 'occupancy',
                   by_category: bool = True, stationary: bool = False):
    """
    Get summary dataframe

    Parameters
    ----------
    hills : dict
        Created by `make_hills`
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
    nonstationary_stub = 'dow_binofday'
    stationary_stub = ''

    flow_metrics = {'a': 'arrivals', 'd': 'departures', 'o': 'occupancy'}
    flow_metric_key = flow_metrics[flow_metric[0].lower()]
    cat_field = hills['settings']['cat_field']

    if stationary:
        time_key = 'stationary'
        if by_category and cat_field is not None:
            cat_key = f'{cat_field}_{stationary_stub}'.rstrip('_')
        else:
            cat_key = f'{stationary_stub}'
    else:
        time_key = 'nonstationary'
        if by_category and cat_field is not None:
            cat_key = f'{cat_field}_{nonstationary_stub}'.rstrip('_')
        else:
            cat_key = f'{nonstationary_stub}'

    try:
        df = hills['summaries'][time_key][cat_key][flow_metric_key]
        return df
    except KeyError as error:
        print(f'Key does not exist.\n{error}')
        return None


def get_bydatetime_df(hills: dict, by_category: bool = True):
    """
    Get summary dataframe

    Parameters
    ----------
    hills : dict
        Created by `make_hills`
    by_category : bool
        Default=True corresponds to category specific statistics. A value of False gives overall statistics.


    Returns
    -------
    DataFrame

    """
    bydatetime_stub = 'datetime'
    cat_field = hills['settings']['cat_field']

    if by_category and cat_field is not None:
        cat_key = f'{cat_field}_{bydatetime_stub}'.rstrip('_')
    else:
        cat_key = f'{bydatetime_stub}'

    try:
        df = hills['bydatetime'][cat_key]
        return df
    except KeyError as error:
        print(f'Key does not exist.\n{error}')
        return None


def get_los_plot(hills: dict, by_category: bool = True):
    """
    Get length of stay histogram from length of stay summary

    Parameters
    ----------
    hills : dict
        Created by `make_hills`
    by_category : bool
        Default=True corresponds to category specific statistics. A value of False gives overall statistics.

    Returns
    -------
    plot object from matplotlib

    """

    if by_category:
        plot = hills['los_summary']['los_histo_bycat']
    else:
        plot = hills['los_summary']['los_histo']

    return plot


def get_los_stats(hills: dict, by_category: bool = True):
    """
    Get stats from length of stay summary

    Parameters
    ----------
    hills : dict
        Created by `make_hills`
    by_category : bool
        Default=True corresponds to category specific statistics. A value of False gives overall statistics.

    Returns
    -------
    pandas Styler object

    """

    if by_category:
        stats = hills['los_summary']['los_stats_bycat']
    else:
        stats = hills['los_summary']['los_stats']

    return stats


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
            file_summary_csv_stem = f'{scenario_name}_{metric}'
            if len(d) > 0:
                file_summary_csv = f'{file_summary_csv_stem}_{d}.csv'
            else:
                # Stationary overall
                file_summary_csv = f'{file_summary_csv_stem}.csv'

            Path(export_path).mkdir(parents=True, exist_ok=True)
            csv_wpath = Path(export_path, file_summary_csv)

            df.to_csv(csv_wpath, index=False, float_format='%.6f')
