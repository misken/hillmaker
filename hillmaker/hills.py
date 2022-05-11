"""Hillmaker"""

# Copyright 2015 Mark Isken
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

import os
from pathlib import Path

import pandas as pd

from bydatetime import make_bydatetime
from summarize import summarize
from hmlib import HillTimer


def make_hills(scenario_name, stops_df, infield, outfield,
               start_analysis_dt_ts, end_analysis_dt_ts,
               catfield=None,
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
               verbose=0):
    """
    Compute occupancy, arrival, and departure statistics by time bin of day and day of week.

    Main function that first calls `bydatetime.make_bydatetime` to calculate occupancy, arrival
    and departure values by date by time bin and then calls `summarize.summarize`
    to compute the summary statistics.

    Parameters
    ----------

    scenario_name : string
        Used in output filenames
    stops_df : DataFrame
        Base data containing one row per visit
    infield : string
        Column name corresponding to the arrival times
    outfield : string
        Column name corresponding to the departure times
    start_analysis_dt_ts : datetime-like, str
        Starting datetime for the analysis (must be convertible to pandas Timestamp)
    end_analysis_dt_ts : datetime-like, str
        Ending datetime for the analysis (must be convertible to pandas Timestamp)
    catfield : string or List of strings, optional
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
    export_path : string, optional
        Destination path for exported csv files, default is current directory
    verbose : int, optional
        The verbosity level. The default, zero, means silent mode. Higher numbers mean more output messages.

    Returns
    -------
    dict of DataFrames
       The bydatetime DataFrames and all summary DataFrames.
    """

    start_analysis_dt_ts = pd.Timestamp(start_analysis_dt_ts)
    end_analysis_dt_ts = pd.Timestamp(end_analysis_dt_ts)

    start_analysis_dt_np = start_analysis_dt_ts.to_datetime64()
    end_analysis_dt_np = end_analysis_dt_ts.to_datetime64()

    # Filter out records that don't overlap the analysis span
    stops_df = stops_df.loc[(stops_df[infield] <= end_analysis_dt_ts) & (stops_df[outfield] >= start_analysis_dt_ts)]

    # Create the bydatetime DataFrame
    with HillTimer() as t:
        starttime = t.start
        bydt_dfs = make_bydatetime(stops_df,
                                   infield,
                                   outfield,
                                   start_analysis_dt_np,
                                   end_analysis_dt_np,
                                   catfield,
                                   bin_size_minutes,
                                   cat_to_exclude=cat_to_exclude,
                                   occ_weight_field=occ_weight_field,
                                   edge_bins=edge_bins,
                                   totals=totals,
                                   verbose=verbose)

    if verbose:
        print("Datetime matrix created (seconds): {:.4f}".format(t.interval))

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

        if verbose:
            print("Summaries by datetime created (seconds): {:.4f}".format(t.interval))

    # Export results to csv if requested
    if export_bydatetime_csv:
        with HillTimer() as t:

            export_bydatetimes(bydt_dfs, scenario_name, export_path)

        if verbose:
            print("By datetime exported to csv (seconds): {:.4f}".format(t.interval))

    if export_summaries_csv:
        with HillTimer() as t:

            if nonstationary_stats:
                export_summaries(summary_dfs, scenario_name, export_path, 'nonstationary')

            if stationary_stats:
                export_summaries(summary_dfs, scenario_name, export_path, 'stationary')

        if verbose:
            print("Summaries exported to csv (seconds): {:.4f}".format(t.interval))

    # All done

    hills = {'bydatetime': bydt_dfs, 'summaries': summary_dfs}

    endtime = t.end

    if verbose:
        print("Total time (seconds): {:.4f}".format(endtime - starttime))

    return hills


def export_bydatetimes(bydt_dfs, scenario_name, export_path):
    """
    Export bydatetime DataFrames to csv files.


    Parameters
    ----------
    bydt_dfs: dict of DataFrames
        Output from make_hills to be exported

    scenario_name: string
        Used in output filenames

    export_path: string
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

    # Create the parser
    parser = argparse.ArgumentParser(prog='simerlang',
                                     description='Generate erlang random variates')

    # Add arguments
    parser.add_argument(
        '-k', type=int, default=1,
        help="Number of stages in erlang distribution (default is 1)"
    )

    parser.add_argument(
        '-b', type=float, default=1.0,
        help="Overall mean of erlang distribution (i.e., each stage has mean b/k). (default is 1.0)"
    )

    parser.add_argument(
        '-n', type=int, default=1,
        help="Number of random variates to generate (default is 1)"
    )

    parser.add_argument(
        '--scenario', type=str, default=f'scen{datetime.now():%Y%m%d%H%M}',
        help="String used in output filenames"
    )

    parser.add_argument(
        '-o', '--output', type=str, default=sys.stdout,
        help="Path to directory in which to output files"
    )

    parser.add_argument(
        '-s', type=int, default=None,
        help="Random number generator seed (default is None)"
    )

    parser.add_argument(
        '--config', type=str, default=None,
        help="Configuration file containing input parameter arguments and values"
    )

    parser.add_argument("--loglevel", default='WARNING',
                        help="Use valid values for logging package (default is 'WARNING")

    # Do the parsing and return the populated namespace with the input arg values
    # If argv == None, then ``parse_args`` will use ``sys.argv[1:]``.
    # By including ``argv=None`` as input to ``main``, our program can be
    # imported and ``main`` called with arguments. This will be useful for
    # testing via pytest.
    args = parser.parse_args(argv)
    return args


def update_args(args, config):
    """
    Update args namespace values from config dictionary
    Parameters
    ----------
    args : namespace
    config : dict
    Returns
    -------
    Updated args namespace
    """

    # Convert args namespace to a dict
    args_dict = vars(args)

    # Update args dict from config dict
    for key in config.keys():
        args_dict[key] = config[key]

    # Convert dict to updated namespace
    args = argparse.Namespace(**args_dict)
    return args


def generate_rvs(k=1, b=1, n=1, seed=None):
    """
    Parameters
    ----------
    k : int, number of stages (default is 1)
    b : float, overall mean of erlang distribution (default is 1)
    n : int, number of erlang variates to generate (default is 1)
    seed : int, seed for random number generator (default is None)
    Returns
    -------
    samples : ndarray
    """
    if seed is None:
        logging.warning("No random number generator seed specified.")

    rng = default_rng(seed)
    logging.info(f'k={k}, b={b}, n={n}')
    rvs = rng.gamma(shape=k, scale=b / k, size=n)

    return rvs


def main(argv=None):
    """
    :param argv:
    :return:
    """
    # Set logging level
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    # Get input arguments
    args = process_command_line(argv)

    logger = logging.getLogger()
    logger.setLevel(args.loglevel)

    # Update input args if config file passed
    if args.config is not None:
        # Read inputs from config file
        with open(args.config, 'rt') as yaml_file:
            yaml_config = yaml.safe_load(yaml_file)
            args = update_args(args, yaml_config)

    logger.info(args)

    dfs = make_hills(scenario, ss_df, in_fld_name, out_fld_name,
                      start_a, end_a, catfield=cat_fld_name,
                      export_path=output_path, verbose=verbose)

    # Handle output
    if args.output is not None:
        simio.rvs_tocsv(erlang_variates, args)
        print(erlang_variates)
    else:
        print(erlang_variates)

    return 0


if __name__ == '__main__':
    sys.exit(main())





    #
    #
    # # Required inputs
    # rectypes = False
    #
    # if rectypes:
    #     scenario = 'rectypes'
    #     in_fld_name = 'InRoomTS'
    #     out_fld_name = 'OutRoomTS'
    #     #cat_fld_name = 'PatType'
    #     cat_fld_name = None
    #     start_a = '1/1/1996'
    #     end_a = '1/3/1996 23:45'
    #     file_stopdata = './data/rectypes.csv'
    #     # Optional inputs
    #     verbose = 2
    #     output_path = Path('./output')
    # else:
    #     scenario = 'ss_ex05'
    #     in_fld_name = 'InRoomTS'
    #     out_fld_name = 'OutRoomTS'
    #     cat_fld_name = 'PatType'
    #     start_a = '1/1/1996'
    #     end_a = '3/30/1996 23:45'
    #     file_stopdata = './data/ShortStay.csv'
    #     # Optional inputs
    #     verbose = 1
    #     output_path = Path('./output')
    #
    # # Create dfs
    # ss_df = pd.read_csv(file_stopdata, parse_dates=[in_fld_name, out_fld_name], comment='#')
    #
    # dfs = make_hills(scenario, ss_df, in_fld_name, out_fld_name,
    #                  start_a, end_a, catfield=cat_fld_name,
    #                  export_path=output_path, verbose=verbose)
    #
    # print(dfs.keys())
