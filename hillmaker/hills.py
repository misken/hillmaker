"""Hillmaker"""

# Copyright 2015, 2022 Mark Isken
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from pathlib import Path
import argparse
import logging

import pandas as pd

from hillmaker.bydatetime import make_bydatetime
from hillmaker.summarize import summarize
from hillmaker.hmlib import HillTimer


def make_hills(scenario_name, stops_df, in_field, out_field,
               start_analysis_dt, end_analysis_dt,
               cat_field=None,
               bin_size_minutes=60,
               percentiles=(0.25, 0.5, 0.75, 0.95, 0.99),
               cat_to_exclude=None,
               occ_weight_field=None,
               totals=1,
               nonstationary_stats=True,
               stationary_stats=True,
               export_bydatetime_csv=True,
               export_summaries_csv=True,
               export_path=Path('.'),
               edge_bins=1,
               verbose=1):
    """
    Compute occupancy, arrival, and departure statistics by category, time bin of day and day of week.

    Main function that first calls `bydatetime.make_bydatetime` to calculate occupancy, arrival
    and departure values by date by time bin and then calls `summarize.summarize`
    to compute the summary statistics.

    Parameters
    ----------

    scenario_name : string
        Used in output filenames
    stops_df : DataFrame
        Base data containing one row per visit
    in_field : string
        Column name corresponding to the arrival times
    out_field : string
        Column name corresponding to the departure times
    start_analysis_dt : datetime-like, str
        Starting datetime for the analysis (must be convertible to pandas Timestamp)
    end_analysis_dt : datetime-like, str
        Ending datetime for the analysis (must be convertible to pandas Timestamp)
    cat_field : string or List of strings, optional
        Column name(s) corresponding to the categories. If none is specified, then
        only overall occupancy is analyzed.
        Default is None
    bin_size_minutes : int, optional
        Number of minutes in each time bin of the day, default is 60
    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)
    cat_to_exclude : list, optional
        Categories to ignore, default is None
    occ_weight_field : string, optional
        Column name corresponding to the weights to use for occupancy incrementing.
    edge_bins: int, default 1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=whole bin
    totals: int, default 1
        0=no totals, 1=totals by datetime
    nonstationary_stats : bool, optional
       If True, datetime bin stats are computed. Else, they aren't computed. Default is True
    stationary_stats : bool, optional
       If True, overall, non time bin dependent, stats are computed. Else, they aren't computed. Default is True
    export_bydatetime_csv : bool, optional
       If True, bydatetime DataFrames are exported to csv files. Default is True.
    export_summaries_csv : bool, optional
       If True, summary DataFrames are exported to csv files. Default is True.
    export_path : str or Path, optional
        Destination path for exported csv files, default is current directory
    verbose : int, optional
        Used to set level in loggers. 1=logging.INFO, 0=logging.WARNING (default=1)

    Returns
    -------
    dict of DataFrames
       The bydatetime DataFrames and all summary DataFrames.
    """

    # Reconfgure root logger if necessary
    if not verbose:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.WARNING)

    # This should inherit level from root logger
    logger = logging.getLogger(__name__)

    # pandas Timestamp versions of analysis span end points
    start_analysis_dt_ts = pd.Timestamp(start_analysis_dt)
    end_analysis_dt_ts = pd.Timestamp(end_analysis_dt)

    # numpy datetime64 versions of analysis span end points
    start_analysis_dt_np = start_analysis_dt_ts.to_datetime64()
    end_analysis_dt_np = end_analysis_dt_ts.to_datetime64()

    # Filter out records that don't overlap the analysis span
    stops_df = stops_df.loc[(stops_df[in_field] <= end_analysis_dt_ts) & (stops_df[out_field] >= start_analysis_dt_ts)]

    # reset index of df to ensure sequential numbering
    stops_df = stops_df.reset_index(drop=True)

    # Create the bydatetime DataFrame
    with HillTimer() as t:
        starttime = t.start
        bydt_dfs = make_bydatetime(stops_df,
                                   in_field,
                                   out_field,
                                   start_analysis_dt_np,
                                   end_analysis_dt_np,
                                   cat_field,
                                   bin_size_minutes,
                                   cat_to_exclude=cat_to_exclude,
                                   occ_weight_field=occ_weight_field,
                                   edge_bins=edge_bins,
                                   totals=totals,
                                   verbose=verbose)

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
                                    verbose=verbose)

        logger.info(f"Summaries by datetime created (seconds): {t.interval:.4f}")

    # Export results to csv if requested
    if export_bydatetime_csv:
        with HillTimer() as t:
            export_bydatetime(bydt_dfs, scenario_name, export_path)

        logger.info(f"By datetime exported to csv (seconds): {t.interval:.4f}")

    if export_summaries_csv:
        with HillTimer() as t:
            if nonstationary_stats:
                export_summaries(summary_dfs, scenario_name, export_path, 'nonstationary')
            if stationary_stats:
                export_summaries(summary_dfs, scenario_name, export_path, 'stationary')

        logger.info(f"Summaries exported to csv (seconds): {t.interval:.4f}")

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
        csv_wpath = Path(export_path, file_bydt_csv)

        dt_cols = ['arrivals', 'departures', 'occupancy',
                   'day_of_week', 'dow_name', 'bin_of_day', 'bin_of_week']

        bydt_dfs[d].to_csv(csv_wpath, index=True, float_format='%.6f', columns=dt_cols)


def export_summaries(summary_all_dfs, scenario_name, export_path, temporal_key):
    """
    Export occupancy, arrival, and departure summary DataFrames to csv files.


    Parameters
    ----------
    summary_all_dfs: dict of DataFrames
        Output from make_hills to be exported

    scenario_name: string
        Used in output filenames

    export_path: string
        Destination path for exported csv files

    temporal_key: string
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
        scenario_name : string
        Used in output filenames
    stops_df : DataFrame
        Base data containing one row per visit
    infield : string
        Column name corresponding to the arrival times
    outfield : string
        Column name corresponding to the departure times
    start_analysis_dt : datetime-like, str
        Starting datetime for the analysis (must be convertible to pandas Timestamp)
    end_analysis_dt : datetime-like, str
        Ending datetime for the analysis (must be convertible to pandas Timestamp)
    catfield : str, optional
        Column name(s) corresponding to the categories. If none is specified, then
        only overall occupancy is analyzed.
        Default is None
    bin_size_minutes : int, optional
        Number of minutes in each time bin of the day, default is 60
    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)
    cat_to_exclude : list, optional
        Categories to ignore, default is None
    occ_weight_field : string, optional
        Column name corresponding to the weights to use for occupancy incrementing.
    edge_bins: int, default 1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=whole bin
    totals: int, default 1
        0=no totals, 1=totals by datetime, 2=totals bydatetime as well as totals for each field in the
        catfields (only relevant for > 1 category field)
    nonstationary_stats : bool, optional
       If True, datetime bin stats are computed. Else, they aren't computed. Default is True
    stationary_stats : bool, optional
       If True, overall, non time bin dependent, stats are computed. Else, they aren't computed. Default is True
    export_bydatetime_csv : bool, optional
       If True, bydatetime DataFrames are exported to csv files. Default is True.
    export_summaries_csv : bool, optional
       If True, summary DataFrames are exported to csv files. Default is True.
    export_path : str or Path, optional
        Destination path for exported csv files, default is current directory
    verbose : int, optional
        The verbosity level. The default, zero, means silent mode. Higher numbers mean more output messages.
    """

    # Create the parser
    parser = argparse.ArgumentParser(prog='hillmaker',
                                     description='Occupancy analysis by time of day and day of week')

    # Add arguments
    parser.add_argument(
        'scenario', type=str,
        help="Used in output filenames"
    )

    parser.add_argument(
        'stop_data_csv', type=str,
        help="Path to csv file containing the stop data to be processed"
    )

    parser.add_argument(
        'in_field', type=str,
        help="Column name corresponding to the arrival times"
    )

    parser.add_argument(
        'out_field', type=str,
        help="Column name corresponding to the departure times"
    )

    parser.add_argument(
        'start_analysis_dt', type=str,
        help="Starting datetime for the analysis (must be convertible to pandas Timestamp)"
    )

    parser.add_argument(
        'end_analysis_dt', type=str,
        help="Ending datetime for the analysis (must be convertible to pandas Timestamp)"
    )

    parser.add_argument(
        '--cat_field', type=str, default=None,
        help="Column name corresponding to the categories. If None, then only overall occupancy is analyzed"
    )

    parser.add_argument(
        '--bin_size_mins', type=int, default=60,
        help="Number of minutes in each time bin of the day"
    )

    parser.add_argument(
        '--occ_weight_field', type=str, default=None,
        help="Column name corresponding to occupancy weights. If None, then weight of 1.0 is used"
    )

    parser.add_argument(
        '--edge_bins', type=int, default=1,
        help="Occupancy contribution method for arrival and departure bins. 1=fractional, 2=whole bin"
    )

    parser.add_argument(
        '--no_totals', action='store_true',
        help="Use to suppress totals (default is False)"
    )

    parser.add_argument(
        '--output_path', type=str, default='.',
        help="Destination path for exported csv files, default is current directory."
    )

    parser.add_argument(
        '--verbose', type=int, default=1,
        help="Used to set level in loggers. 1=logging.INFO, 0=logging.WARNING (default=1)"
    )

    # Do the parsing and return the populated namespace with the input arg values
    # If argv == None, then ``parse_args`` will use ``sys.argv[1:]``.
    args = parser.parse_args(argv)
    return args


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

    # Read in stop data to DataFrame
    stops_df = pd.read_csv(args.stop_data_csv, parse_dates=[args.in_field, args.out_field])

    # Make hills
    dfs = make_hills(args.scenario, stops_df, args.in_field,  args.out_field,
                     args.start_analysis_dt, args.end_analysis_dt, cat_field=args.cat_field,
                     export_path=args.output_path, verbose=args.verbose)


if __name__ == '__main__':
    sys.exit(main())


