import sys
from argparse import ArgumentParser, Namespace, SUPPRESS

import pandas as pd

from hillmaker.scenario import update_params_from_toml
from hillmaker import Scenario

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

"""
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
        Number of minutes in each time bin of the day, default is 60. This bin size is used for plots and reporting and
        is an aggregation of computations done at the finer bin size resolution specified by `resolution_bin_size_mins`.
        Use a value that divides into 1440 with no remainder.
    cats_to_exclude : list, optional
        Category values to ignore, default is None
    occ_weight_field : str, optional
        Column name corresponding to the weights to use for occupancy incrementing, default is None
        which corresponds to a weight of 1.0
    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)
    los_units : str, optional
        The time units for length of stay analysis.
        See https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.html for allowable values (smallest
        value allowed is 'seconds', largest is 'days'. The default is 'hours'.

    export_bydatetime_csv : bool, optional
       If True, bydatetime DataFrames are exported to csv files. Default is False.
    export_summaries_csv : bool, optional
       If True, summary DataFrames are exported to csv files. Default is False.
    csv_export_path : str or Path, optional
        Destination path for exported csv and png files, default is current directory

    make_all_dow_plots : bool, optional
       If True, day of week plots are created for occupancy, arrival, and departure. Default is True.
    make_all_week_plots : bool, optional
       If True, full week plots are created for occupancy, arrival, and departure. Default is True.
    export_all_dow_plots : bool, optional
       If True, day of week plots are exported for occupancy, arrival, and departure. Default is False.
    export_all_week_plots : bool, optional
       If True, full week plots are exported for occupancy, arrival, and departure. Default is False.
    plot_export_path : str or None, default is None
        If not None, plot is exported to `export_path`

    plot_style : str, optional
        Matplotlib built in style name. Default is 'ggplot'.
    figsize : Tuple, optional
        Figure size. Default is (15, 10)
    bar_color_mean : str, optional
        Matplotlib color name for the bars representing mean values. Default is 'steelblue'
    plot_percentiles : list or tuple of floats (e.g. [0.75, 0.95]), optional
        Which percentiles to plot. Default is (0.95)
    pctile_color : list or tuple of color codes (e.g. ['blue', 'green'] or list('gb'), optional
        Line color for each percentile series plotted. Order should match order of percentiles list.
        Default is ('black', 'grey').
    pctile_linestyle : List or tuple of line styles (e.g. ['-', '--']), optional
        Line style for each percentile series plotted. Default is ('-', '--').
    pctile_linewidth : List or tuple of line widths in points (e.g. [1.0, 0.75])
        Line width for each percentile series plotted. Default is (0.75, 0.75).
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
    first_dow : str, optional
        Controls which day of week appears first in plot. One of 'mon', 'tue', 'wed', 'thu', 'fri', 'sat, 'sun'

    edge_bins: int, default 1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=entire bin
    highres_bin_size_minutes : int, optional
        Number of minutes in each time bin of the day used for initial computation of the number of arrivals,
        departures, and the occupancy level. This value should be <= `bin_size_minutes`. The shorter the duration of
        stays, the smaller the resolution should be. The current default is 5 minutes.
    keep_highres_bydatetime : bool, optional
        Save the high resolution bydatetime dataframe in hills attribute. Default is False.
    nonstationary_stats : bool, optional
       If True, datetime bin stats are computed. Else, they aren't computed. Default is True
    stationary_stats : bool, optional
       If True, overall, non-time bin dependent, stats are computed. Else, they aren't computed. Default is True
    verbosity : int, optional
        Used to set level in loggers. 0=logging.WARNING (default=0), 1=logging.INFO, 2=logging.DEBUG
"""
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

    # CSV export options
    optional.add_argument(
        '--export_bydatetime_csv', type=bool, default=True,
        help="If True, bydatetime DataFrames are exported to csv files."
    )

    optional.add_argument(
        '--export_summaries_csv', type=bool, default=True,
        help="If True, summary DataFrames are exported to csv files."
    )

    optional.add_argument(
        '--csv_export_path', type=str, default='.',
        help="Destination path for exported csv files, default is current directory."
    )

    # Plot export options
    optional.add_argument(
        '--make_all_dow_plots', type=bool, default=True,
        help="If True, day of week plots are created for occupancy, arrivals, and departures and exported to plot_export_path."
    )

    optional.add_argument(
        '--make_all_week_plots', type=bool, default=True,
        help="If True, full week plots are created for occupancy, arrivals, and departures and exported to plot_export_path."
    )

    optional.add_argument(
        '--export_all_dow_plots', type=bool, default=True,
        help="If True, day of week plots are for occupancy, arrivals, and departures."
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
        nargs="2",  # 0 or more values expected => creates a list
        type=int,
        default=(15, 10),
        help="Figure size"
    )

    optional.add_argument(
        '--bar_color_mean', type=str, default='steelblue',
        help="Matplotlib color name for the bars representing mean values."
    )

    optional.add_argument(
        "--plot_percentiles",
        nargs="*",  # 0 or more values expected => creates a list
        type=float,
        default=(0.95, 0.75),
        help="Which percentiles to plot"
    )

    optional.add_argument(
        "--pctile_color",
        nargs="*",  # 0 or more values expected => creates a list
        type=str,
        default=('black', 'grey'),
        help="Line color for each percentile series plotted. Order should match order of percentiles list."
    )

    optional.add_argument(
        "--pctile_linestyle",
        nargs="*",  # 0 or more values expected => creates a list
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
        '--main_title', type=str, default='{Occupancy, Arrivals, Departures} by time of day and day of week',
        help="Main title for plot"
    )

    optional.add_argument(
        '--subtitle', type=str, default='Scenario: {scenario_name}',
        help="Subtitle for plot"
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

    # edge_bins: int, default 1
    #     Occupancy contribution method for arrival and departure bins. 1=fractional, 2=entire bin
    # highres_bin_size_minutes : int, optional
    #     Number of minutes in each time bin of the day used for initial computation of the number of arrivals,
    #     departures, and the occupancy level. This value should be <= `bin_size_minutes`. The shorter the duration of
    #     stays, the smaller the resolution should be. The current default is 5 minutes.
    # keep_highres_bydatetime : bool, optional
    #     Save the high resolution bydatetime dataframe in hills attribute. Default is False.
    # nonstationary_stats : bool, optional
    #    If True, datetime bin stats are computed. Else, they aren't computed. Default is True
    # stationary_stats : bool, optional
    #    If True, overall, non-time bin dependent, stats are computed. Else, they aren't computed. Default is True

    # Advanced optional arguments
    optional.add_argument(
        '--edge_bins', type=int, default=1,
        help="Occupancy contribution method for arrival and departure bins. 1=fractional, 2=entire bin"
    )

    optional.add_argument(
        '--highres_bin_size_minutes', type=int, default=5,
        help="""Number of minutes in each time bin of the day used for initial computation of the number of arrivals,
         departures, and the occupancy level. This value should be <= `bin_size_minutes`. The shorter the duration of
         stays, the smaller the resolution should be if using edge_bins=2. See docs for more details."""
    )

    optional.add_argument(
        '--keep_highres_bydatetime', type=bool, default=False,
        help="Save the high resolution bydatetime dataframe in hills attribute."
    )

    optional.add_argument(
        '--nonstationary_stats', type=bool, default=True,
        help=" If True, datetime bin stats are computed."
    )

    optional.add_argument(
        '--stationary_stats', type=bool, default=True,
        help="If True, overall, non-time bin dependent, stats are computed."
    )







    optional.add_argument(
        '--verbosity', type=int, default=1,
        help="Used to set level in loggers. 0=logging.WARNING, 1=logging.INFO (default), 2=logging.DEBUG"
    )

    # Be nice if this default came from application settings file

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

    # Set plot creation and export flags
    if not args.make_all_dow_plots:
        make_dow_plots = True
        export_dow_plots = True
    else:
        make_dow_plots = False
        export_dow_plots = False

    if not args.make_all_week_plots:
        make_week_plot = True
        export_week_plot = True
    else:
        make_week_plot = False
        export_week_plot = False

    scenario = Scenario(scenario_name=args.scenario_name, stops_df=stops_df,
                        in_field=args.in_field, out_field=args.out_field,
                        start_analysis_dt=args.start_analysis_dt, end_analysis_dt=args.end_analysis_dt,
                        cat_field=args.cat_field, bin_size_minutes=args.bin_size_mins,
                        csv_export_path=args.output_path, plot_export_path=args.output_path,
                        verbosity=args.verbosity,
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
