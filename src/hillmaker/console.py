import sys
from argparse import ArgumentParser, Namespace, SUPPRESS

import pandas as pd

from hillmaker.utils import update_params_from_toml
from hillmaker import Scenario

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


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
    parser = ArgumentParser(prog='hillmaker',
                            description='Occupancy analysis by time of day and day of week',
                            add_help=False)

    required = parser.add_argument_group('required arguments (either on command line or via config file)')
    optional = parser.add_argument_group('optional arguments')

    # Add arguments
    required.add_argument(
        '--scenario_name', type=str,
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
        help="Starting datetime for the analysis (use yyyy-mm-dd format)"
    )

    required.add_argument(
        '--end_analysis_dt', type=str,
        help="Ending datetime for the analysis (use yyyy-mm-dd format)"
    )

    optional.add_argument(
        '--config', type=str, default=None,
        help="Configuration file (TOML format) containing input parameter arguments and values."
    )

    optional.add_argument(
        '--cat_field', type=str, default=None,
        help="Column name corresponding to the categories. If None, then only overall occupancy is analyzed."
    )

    optional.add_argument(
        '--bin_size_mins', type=int, default=60,
        help="Number of minutes in each time bin of the day (default=60) for aggregate statistics and plots."
    )

    optional.add_argument(
        '--occ_weight_field', type=str, default=None,
        help="Column name corresponding to occupancy weights. If None, then weight of 1.0 is used. Default is None."
    )

    optional.add_argument(
        '--output_path', type=str, default='.',
        help="Destination path for exported csv files, default is current directory."
    )

    optional.add_argument(
        '--no_plots', action='store_true',
        help="If set (true), all plots are suppressed. By default, plots are exported to OUTPUT_PATH."

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
        '--cap', type=int, default=None,
        help="Capacity level line to include in occupancy plots"
    )

    optional.add_argument(
        '--verbosity', type=int, default=1,
        help="Used to set level in loggers. 0=logging.WARNING, 1=logging.INFO (default), 2=logging.DEBUG"
    )

    # Be nice if this default came from application settings file
    # optional.add_argument(
    #     "--percentiles",
    #     nargs="*",  # 0 or more values expected => creates a list
    #     type=float,
    #     default=(0.25, 0.5, 0.75, 0.95, 0.99),  # default if nothing is provided
    # )
    #
    # optional.add_argument(
    #     "--cats_to_exclude",
    #     nargs="*",  # 0 or more values expected => creates a list
    #     type=str,
    #     default=[],  # default if nothing is provided
    # )

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


def update_args_from_toml(args, toml_dict):
    """
    Update args namespace values from toml_config dictionary

    Parameters
    ----------
    args : namespace
    toml_dict : dict from loading TOML config file

    Returns
    -------
    Updated args namespace
    """

    # Convert args namespace to a dict
    args_dict = vars(args)

    # Flatten toml config (we know there are no key clashes and only one nesting level)
    # Update args dict from config dict
    args_dict = update_params_from_toml(args_dict, toml_dict)

    # Convert dict to updated namespace
    args = Namespace(**args_dict)
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

    # Update input args if config file passed
    if args.config is not None:
        # Read inputs from config file
        with open(args.config, mode="rb") as toml_file:
            toml_config = tomllib.load(toml_file)
            args = update_args_from_toml(args, toml_config)

    # Make sure all required args are specified
    check_for_required_args(args)

    # Read in stop data to DataFrame
    stops_df = pd.read_csv(args.stop_data_csv, parse_dates=[args.in_field, args.out_field])

    # Make hills
    if not args.no_plots:
        make_week_plot = True
        make_dow_plots = True
        export_week_plot = True
        export_dow_plots = True
    else:
        make_week_plot = False
        make_dow_plots = False
        export_week_plot = False
        export_dow_plots = False

    scenario = Scenario(scenario_name=args.scenario_name, stops_df=stops_df,
                        in_field=args.in_field, out_field=args.out_field,
                        start_analysis_dt=args.start_analysis_dt, end_analysis_dt=args.end_analysis_dt,
                        cat_field=args.cat_field, bin_size_minutes=args.bin_size_mins,
                        output_path=args.output_path, verbosity=args.verbosity,
                        export_bydatetime_csv=True, export_summaries_csv=True,
                        make_all_week_plots=make_week_plot, make_all_dow_plots=make_dow_plots,
                        export_all_week_plots=export_week_plot,
                        export_all_dow_plots=export_dow_plots,
                        cap=args.cap, xlabel=args.xlabel, ylabel=args.ylabel,
                        los_units='hours')

    scenario.make_hills()


def check_for_required_args(args):
    """

    Parameters
    ----------
    args: Namespace

    Returns
    -------
    Raises ValueError if a required arg is missing

    """

    # Make sure all required args are present
    required_args = ['scenario_name', 'stop_data_csv', 'in_field', 'out_field',
                     'start_analysis_dt', 'start_analysis_dt']
    # Convert args namespace to a dict
    args_dict = vars(args)
    for req_arg in required_args:
        if args_dict[req_arg] is None:
            raise ValueError(f'{req_arg} is required')


if __name__ == '__main__':
    sys.exit(main())
