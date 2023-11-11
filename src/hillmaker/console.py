"""
The :mod:`hillmaker.console` module provides a command line interface for using hillmaker.
"""

import sys
from argparse import ArgumentParser, Namespace, SUPPRESS

from hillmaker.scenario import update_params_from_toml, create_scenario

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

    required = parser.add_argument_group('Required arguments (either on command line or via config file)')
    optional = parser.add_argument_group('Optional arguments')
    advanced_optional = parser.add_argument_group('Advanced optional arguments')

    # Add arguments
    required.add_argument(
        '--scenario_name', type=str,
        help="Used in output filenames"
    )

    required.add_argument(
        '--data', type=str,
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

    # Optional general arguments
    optional.add_argument(
        '--config', type=str, default=None,
        help="""Configuration file (TOML format) containing input parameter arguments and values. 
        Input parameters set via command line arguments will override parameters values set via the config file."""
    )

    optional.add_argument(
        '--cat_field', type=str, default=None,
        help="Column name corresponding to the categories. If None, then only overall occupancy is analyzed."
    )

    optional.add_argument(
        '--bin_size_minutes', type=int, default=60,
        help="Number of minutes in each time bin of the day (default=60) for aggregate statistics and plots."
    )

    optional.add_argument(
        "--cats_to_exclude",
        nargs="*",  # 0 or more values expected => creates a list
        type=str,
        default=None,  # default if nothing is provided
        help="Category values to exclude from the analysis."
    )

    optional.add_argument(
        '--occ_weight_field', type=str, default=None,
        help="Column name corresponding to occupancy weights. If None, then weight of 1.0 is used. Default is None."
    )

    optional.add_argument(
        "--percentiles",
        nargs="*",  # 0 or more values expected => creates a list
        type=float,
        default=(0.25, 0.5, 0.75, 0.95, 0.99),
        help="Which percentiles to compute"
    )

    optional.add_argument(
        '--los_units', type=str, default='hours',
        help="""The time units for length of stay analysis.
        See https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.html for allowable values (smallest
        value allowed is 'seconds', largest is 'days'. The default is 'hours'."""
    )

    optional.add_argument(
        '--csv_export_path', type=str, default='.',
        help="Destination path for exported csv files, default is current directory."
    )

    # Plot export options
    optional.add_argument(
        '--no_dow_plots', action='store_true',
        help="If set, no day of week plots are created."
    )

    optional.add_argument(
        '--no_week_plots', action='store_true',
        help="If set, no weekly plots are created."
    )

    optional.add_argument(
        '--plot_export_path', type=str, default='.',
        help="Destination path for exported plots, default is current directory."
    )

    # Plot creation options
    optional.add_argument(
        '--plot_style', type=str, default='ggplot',
        help="Matplotlib style name."
    )

    optional.add_argument(
        "--figsize",
        nargs=2,  # 0 or more values expected => creates a list
        type=int,
        default=(15, 10),
        help="Figure size"
    )

    optional.add_argument(
        '--bar_color_mean', type=str, default='steelblue',
        help="Matplotlib color name for the bars representing mean values."
    )

    optional.add_argument(
        '--alpha', type=float, default=0.5,
        help="Transparency for bars, default=0.5."
    )

    optional.add_argument(
        "--plot_percentiles",
        nargs="+",  # 0 or more values expected => creates a list
        type=float,
        default=(0.95, 0.75),
        help="Which percentiles to plot"
    )

    optional.add_argument(
        "--pctile_color",
        nargs="+",  # 0 or more values expected => creates a list
        type=str,
        default=('black', 'grey'),
        help="Line color for each percentile series plotted. Order should match order of percentiles list."
    )

    optional.add_argument(
        "--pctile_linestyle",
        nargs="+",  # 0 or more values expected => creates a list
        type=str,
        default=('-', '--'),
        help="Line style for each percentile series plotted."
    )

    optional.add_argument(
        "--pctile_linewidth",
        nargs="*",  # 0 or more values expected => creates a list
        type=float,
        default=(0.75, 0.75),
        help="Line width for each percentile series plotted."
    )

    optional.add_argument(
        '--cap', type=int, default=None,
        help="Capacity level line to include in occupancy plots"
    )

    optional.add_argument(
        '--cap_color', type=str, default='r',
        help="Matplotlib color code."
    )

    optional.add_argument(
        '--xlabel', type=str, default='Hour',
        help="x-axis label for plots."
    )

    optional.add_argument(
        '--ylabel', type=str, default='Volume',
        help="y-axis label for plots."
    )

    optional.add_argument(
        '--main_title', type=str, default='',
        help="Main title for plot. Default = '{Occupancy, Arrivals, Departures} by time of day and day of week'"
    )

    optional.add_argument(
        '--subtitle', type=str, default='',
        help="Subtitle for plot. Default = 'Scenario: {scenario_name}'"
    )

    optional.add_argument(
        '--first_dow', type=str, default='mon',
        help="Controls which day of week appears first in plot. One of 'mon', 'tue', 'wed', 'thu', 'fri', 'sat, 'sun'"
    )

    # main_title_properties : None or dict, optional
    #     Dict of `suptitle` properties, default={{'loc': 'left', 'fontsize': 16}}
    # subtitle_properties : None or dict, optional
    #     Dict of `title` properties, default={{'loc': 'left', 'style': 'italic'}}
    # legend_properties : None or dict, optional
    #     Dict of `legend` properties, default={{'loc': 'best', 'frameon': True, 'facecolor': 'w'}}

    # Advanced optional arguments
    advanced_optional.add_argument(
        '--edge_bins', type=int, default=1,
        help="Occupancy contribution method for arrival and departure bins. 1=fractional, 2=entire bin"
    )

    advanced_optional.add_argument(
        '--highres_bin_size_minutes', type=int, default=5,
        help="""Number of minutes in each time bin of the day used for initial computation of the number of arrivals,
         departures, and the occupancy level. This value should be <= `bin_size_minutes`. The shorter the duration of
         stays, the smaller the resolution should be if using edge_bins=2. See docs for more details."""
    )

    advanced_optional.add_argument(
        '--keep_highres_bydatetime', action='store_true',
        help="Save the high resolution bydatetime dataframe in hills attribute."
    )

    advanced_optional.add_argument(
        '--verbosity', type=int, default=1,
        help="Used to set level in loggers. 0=logging.WARNING, 1=logging.INFO (default), 2=logging.DEBUG"
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

    # Set plot creation and export flags
    args_dict = vars(args)

    if args.no_dow_plots:
        args_dict['make_all_dow_plots'] = False
        args_dict['export_all_dow_plots'] = False
    else:
        args_dict['make_all_dow_plots'] = True
        args_dict['export_all_dow_plots'] = True
    args_dict.pop('no_dow_plots', None)

    if args.no_week_plots:
        args_dict['make_all_week_plots'] = False
        args_dict['export_all_week_plots'] = False
    else:
        args_dict['make_all_week_plots'] = True
        args_dict['export_all_week_plots'] = True
    args_dict.pop('no_week_plots', None)

    # Set additional args
    args_dict['export_bydatetime_csv'] = True
    args_dict['export_summaries_csv'] = True

    # Update input args if config file passed
    if args.config is not None:
        config_file = args.config
        args_dict.pop('config', None)
        scenario = create_scenario(config_path=config_file, **args_dict)
    else:
        args_dict.pop('config', None)
        scenario = create_scenario(params_dict=args_dict)

    scenario.make_hills()


# def check_for_required_args(args):
#     """
#     Make sure required arguments are present.
#
#     Parameters
#     ----------
#     args: Namespace
#
#     Returns
#     -------
#     Raises ValueError if a required arg is missing
#
#     """
#
#     # Make sure all required args are present
#     required_args = ['scenario_name', 'data', 'in_field', 'out_field',
#                      'start_analysis_dt', 'start_analysis_dt']
#     # Convert args namespace to a dict
#     args_dict = vars(args)
#     for req_arg in required_args:
#         if args_dict[req_arg] is None:
#             raise ValueError(f'{req_arg} is required')


if __name__ == '__main__':
    sys.exit(main())
