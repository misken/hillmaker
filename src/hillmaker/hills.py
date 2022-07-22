"""Hillmaker"""

# Copyright 2022 Mark Isken, Jacob Norman

import sys
from pathlib import Path
from argparse import ArgumentParser, Namespace, SUPPRESS
import logging

import pandas as pd
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


from hillmaker.bydatetime import make_bydatetime
from hillmaker.summarize import summarize
from hillmaker.hmlib import HillTimer
from hillmaker.plotting import export_hill_plot


def setup_logger(verbosity):
    # Set logging level
    root_logger = logging.getLogger()
    root_logger.handlers.clear() # Needed to prevent dup messages when module imported
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


def make_hills(scenario_name, stops_df, in_field, out_field,
               start_analysis_dt, end_analysis_dt,
               cat_field=None,
               bin_size_minutes=60,
               percentiles=(0.25, 0.5, 0.75, 0.95, 0.99),
               cats_to_exclude=None,
               occ_weight_field=None,
               totals=1,
               cap=None,
               nonstationary_stats=True,
               stationary_stats=True,
               no_censored_departures=False,
               export_bydatetime_csv=True,
               export_summaries_csv=True,
               export_dow_png=False,
               export_week_png=False,
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
    totals: int, default 1
        0=no totals, 1=totals by datetime
    cap : int, optional
        Capacity of area being analyzed, default is None
    nonstationary_stats : bool, optional
       If True, datetime bin stats are computed. Else, they aren't computed. Default is True
    stationary_stats : bool, optional
       If True, overall, non time bin dependent, stats are computed. Else, they aren't computed. Default is True
    no_censored_departures: bool, optional
       If True, missing departure datetimes are replaced with datetime of end of analysis range. If False,
       record is ignored. Default is False.
    export_bydatetime_csv : bool, optional
       If True, bydatetime DataFrames are exported to csv files. Default is True.
    export_summaries_csv : bool, optional
       If True, summary DataFrames are exported to csv files. Default is True.
    export_dow_png : bool, optional
       If True, day of week plots are exported for occupancy, arrival, and departure. Default is False.
    export_week_png : bool, optional
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

    # Check if in and out fields are part of stops_df
    if in_field not in list(stops_df):
        raise ValueError(f'Bad in_field - {in_field} is not part of the stops dataframe')

    if out_field not in list(stops_df):
        raise ValueError(f'Bad out_field - {out_field} is not part of the stops dataframe')

    # Check if catfield is part of stops_df
    if cat_field is not None:
        if cat_field not in list(stops_df):
            raise ValueError(f'Bad cat_field - {cat_field} is not part of the stops dataframe')

    # pandas Timestamp versions of analysis span end points
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

    # Update departure timestamp for missing values if no_censored_departures=False
    if not no_censored_departures:
        num_recs_uncensored = num_recs_missing_exit_ts
        if num_recs_missing_exit_ts > 0:
            logger.info(f'{num_recs_missing_exit_ts} records with missing exit timestamps - end of analysis range used for occupancy purposes')
            uncensored_out_field = f'{out_field}_uncensored'
            uncensored_out_value = pd.Timestamp(end_analysis_dt).floor("d") + pd.Timedelta(1, "d")
            stops_df[uncensored_out_field] = stops_df[out_field].fillna(value=uncensored_out_value)
            active_out_field = uncensored_out_field
        else:
            # Records with missing departures will be ignored
            active_out_field = out_field
            if num_recs_missing_exit_ts > 0:
                logger.warning(f'{num_recs_missing_exit_ts} records with missing exit timestamps - records ignored')
    else:
        active_out_field = out_field

    # Filter out records that don't overlap the analysis span or have missing entry timestamps
    stops_df = stops_df.loc[(stops_df[in_field] < end_analysis_dt_ts) &
                            (~stops_df[in_field].isna()) &
                            (stops_df[active_out_field] >= start_analysis_dt_ts)]

    # reset index of df to ensure sequential numbering
    stops_df = stops_df.reset_index(drop=True)

    # Create the bydatetime DataFrame
    with HillTimer() as t:
        starttime = t.start
        bydt_dfs = make_bydatetime(stops_df,
                                   in_field,
                                   active_out_field,
                                   start_analysis_dt_np,
                                   end_analysis_dt_np,
                                   cat_field,
                                   bin_size_minutes,
                                   cat_to_exclude=cats_to_exclude,
                                   occ_weight_field=occ_weight_field,
                                   edge_bins=edge_bins,
                                   totals=totals,
                                   verbosity=verbosity)

    logger.info(f"Datetime matrix created (seconds): {t.interval:.4f}")

    # Create the summary stats DataFrames
    summary_dfs = {}
    if nonstationary_stats or stationary_stats:
        with HillTimer() as t:

            summary_dfs = summarize(bydt_dfs,
                                    nonstationary_stats=nonstationary_stats,
                                    stationary_stats=stationary_stats,
                                    percentiles=percentiles,
                                    totals=totals,
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
    if export_week_png:
        with HillTimer() as t:
            for metric in summary_dfs['nonstationary']['dow_binofday']:
                fullwk_df = summary_dfs['nonstationary']['dow_binofday'][metric]
                fullwk_df = fullwk_df.reset_index()
                export_hill_plot(fullwk_df, scenario_name, metric, export_path=output_path,
                                 bin_size_minutes=bin_size_minutes, cap=cap,
                                 xlabel=xlabel, ylabel=ylabel)

        logger.info(f"Full week plots exported to png (seconds): {t.interval:.4f}")

    # Create and export individual day of week plots if requested
    if export_dow_png:
        with HillTimer() as t:
            for metric in summary_dfs['nonstationary']['dow_binofday']:
                fullwk_df = summary_dfs['nonstationary']['dow_binofday'][metric]
                fullwk_df = fullwk_df.reset_index()
                for dow in fullwk_df['dow_name'].unique():
                    dow_df = fullwk_df.loc[fullwk_df['dow_name'] == dow]
                    export_hill_plot(dow_df, scenario_name, metric, export_path=output_path,
                                     bin_size_minutes=bin_size_minutes, cap=cap, week_range=dow,
                                     xlabel=xlabel, ylabel=ylabel)

        logger.info(f"Individual day of week plots exported to png (seconds): {t.interval:.4f}")

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


def process_command_line(argv=None):
    """
    Parse command line arguments

    Parameters
    ----------
    argv : list of arguments, or `None` for ``sys.argv[1:]``.
    Returns
    ----------
    Namespace representing the argument list.
    """

    """

    """

    # Create the parser
    parser = ArgumentParser(prog='hillmaker',
                                     description='Occupancy analysis by time of day and day of week',
                                     add_help=False)

    required = parser.add_argument_group('required arguments (either on command line or via config file)')
    optional = parser.add_argument_group('optional arguments')

    # Add arguments
    required.add_argument(
        '--scenario', type=str,
        help="Used in output filenames"
    )

    required.add_argument(
        '--stop_data_csv', type=str,
        help="Path to csv file containing the stop data to be processed"
    )

    required.add_argument(
        '--in_field', type=str,
        help="Column name corresponding to the arrival times"
    )

    required.add_argument(
        '--out_field', type=str,
        help="Column name corresponding to the departure times"
    )

    required.add_argument(
        '--start_analysis_dt', type=str,
        help="Starting datetime for the analysis (must be convertible to pandas Timestamp)"
    )

    required.add_argument(
        '--end_analysis_dt', type=str,
        help="Ending datetime for the analysis (must be convertible to pandas Timestamp)"
    )

    optional.add_argument(
        '--config', type=str, default=None,
        help="Configuration file (TOML format) containing input parameter arguments and values"
    )

    optional.add_argument(
        '--cat_field', type=str, default=None,
        help="Column name corresponding to the categories. If None, then only overall occupancy is analyzed"
    )

    optional.add_argument(
        '--bin_size_mins', type=int, default=60,
        help="Number of minutes in each time bin of the day"
    )

    optional.add_argument(
        '--occ_weight_field', type=str, default=None,
        help="Column name corresponding to occupancy weights. If None, then weight of 1.0 is used"
    )

    optional.add_argument(
        '--edge_bins', type=int, default=1,
        help="Occupancy contribution method for arrival and departure bins. 1=fractional, 2=whole bin"
    )

    optional.add_argument(
        '--no_totals', action='store_true',
        help="Use to suppress totals (default is False)"
    )

    optional.add_argument(
        '--output_path', type=str, default='.',
        help="Destination path for exported csv files, default is current directory."
    )

    optional.add_argument(
        '--export_week_png', action='store_true',
        help="If set (true), weekly plots are exported to OUTPUT_PATH"

    )

    optional.add_argument(
        '--export_dow_png', action='store_true',
        help="If set (true), individual day of week plots are exported to OUTPUT_PATH"
    )

    optional.add_argument(
        '--xlabel', type=str, default='Hour',
        help="x-axis label for plots"
    )

    optional.add_argument(
        '--ylabel', type=str, default='Hour',
        help="y-axis label for plots"
    )

    optional.add_argument(
        '--verbosity', type=int, default=0,
        help="Used to set level in loggers. 0=logging.WARNING (default=0), 1=logging.INFO, 2=logging.DEBUG"
    )

    optional.add_argument(
        '--cap', type=int, default=None,
        help="Capacity level line to include in plots"
    )

    optional.add_argument(
        "--percentiles",
        nargs="*",  # 0 or more values expected => creates a list
        type=float,
        default=(0.25, 0.5, 0.75, 0.95, 0.99),  # default if nothing is provided
    )

    optional.add_argument(
        "--cats_to_exclude",
        nargs="*",  # 0 or more values expected => creates a list
        type=str,
        default=[],  # default if nothing is provided
    )

    optional.add_argument(
        '--no_censored_departures', action='store_true',
        help="If set (true), records with missing departure timestamps are ignored. By default, such records are assumed to be still in the system at the end_analysis_dt."
    )

    # Add back help
    optional.add_argument(
        '-h',
        '--help',
        action='help',
        default=SUPPRESS,
    )

    # Do the parsing and return the populated namespace with the input arg values
    # If argv == None, then ``parse_args`` will use ``sys.argv[1:]``.
    args = parser.parse_args(argv)
    return args

def update_args(args, toml_config):
    """
    Update args namespace values from toml_config dictionary

    Parameters
    ----------
    args : namespace
    toml_config : dict from loading TOML config file

    Returns
    -------
    Updated args namespace
    """

    # Convert args namespace to a dict
    args_dict = vars(args)

    # Flatten toml config (we know there are no key clashes and only one nesting level)
    # Update args dict from config dict
    for outerkey, outerval in toml_config.items():
        for key, val in outerval.items():
            args_dict[key] = val

    # Convert dict to updated namespace
    args = Namespace(**args_dict)
    return args

def check_for_required_args(args):
    """

    Parameters
    ----------
    args: Namespace

    Returns
    -------

    """

    # Make sure all required args are present
    required_args = ['scenario', 'stop_data_csv', 'in_field', 'out_field', 'start_analysis_dt', 'start_analysis_dt']
    # Convert args namespace to a dict
    args_dict = vars(args)
    for req_arg in required_args:
        if args_dict[req_arg] is None:
            raise ValueError(f'{req_arg} is required')

def main(argv=None):
    """
    :param argv: Input arguments
    :return: No return value
    """

    # By including ``argv=None`` as input to ``main``, our program can be
    # imported and ``main`` called with arguments. This will be useful for
    # testing via pytest.
    # Get input arguments
    args = process_command_line(argv)

    # Update input args if config file passed
    if args.config is not None:
        # Read inputs from config file
        with open(args.config, mode="rb") as toml_file:
            toml_config = tomllib.load(toml_file)
            args = update_args(args, toml_config)

    # Make sure all required args are specified
    check_for_required_args(args)

    # Read in stop data to DataFrame
    stops_df = pd.read_csv(args.stop_data_csv, parse_dates=[args.in_field, args.out_field])

    # Make hills
    dfs = make_hills(args.scenario, stops_df, args.in_field, args.out_field,
                     args.start_analysis_dt, args.end_analysis_dt, cat_field=args.cat_field,
                     output_path=args.output_path, verbosity=args.verbosity,
                     cats_to_exclude=args.cats_to_exclude, percentiles=args.percentiles,
                     export_week_png=args.export_week_png, export_dow_png=args.export_dow_png,
                     cap=args.cap, xlabel=args.xlabel, ylabel=args.ylabel)


if __name__ == '__main__':
    sys.exit(main())


