from typing import Tuple, List
from pathlib import Path
from datetime import datetime, date
from typing import Dict

import numpy as np
import pandas as pd

from hillmaker.scenario import Scenario, VerbosityEnum
from hillmaker.hills import _make_hills


def make_hills(scenario_name: str,
               stops_df: pd.DataFrame,
               in_field: str, out_field: str,
               start_analysis_dt: str | date | datetime | pd.Timestamp | np.datetime64,
               end_analysis_dt: str | date | datetime | pd.Timestamp | np.datetime64,
               cat_field: str = None,
               bin_size_minutes: int = 60,
               percentiles: Tuple | List = (0.25, 0.5, 0.75, 0.95, 0.99),
               cats_to_exclude: str | None = None,
               occ_weight_field: str | None = None,
               cap: int | None = None,
               los_units: str = 'hours',
               csv_export_path: str | Path = Path('.'),
               export_bydatetime_csv: bool = True,
               export_summaries_csv: bool = True,
               make_all_dow_plots: bool = True,
               make_all_week_plots: bool = True,
               export_dow_plot: bool = True,
               export_week_plot: bool = True,
               plot_style: str = 'ggplot',
               figsize: tuple = (15, 10),
               bar_color_mean: str = 'steelblue',
               plot_percentiles: Tuple[float] | List[float] = (0.95, 0.75),
               pctile_color: Tuple[str] | List[str] = ('black', 'grey'),
               pctile_linestyle: Tuple[str] | List[str] = ('-', '--'),
               pctile_linewidth: Tuple[float] | List[float] = (0.75, 0.75),
               cap_color: str = 'r',
               xlabel: str = 'Hour',
               ylabel: str = 'Volume',
               main_title: str = '',
               main_title_properties: None | Dict = {'loc': 'left', 'fontsize': 16},
               subtitle: str = '',
               subtitle_properties: None | Dict = {'loc': 'left', 'style': 'italic'},
               legend_properties: None | Dict = {'loc': 'best', 'frameon': True, 'facecolor': 'w'},
               first_dow: str = 'mon',
               plot_export_path: Path | str | None = None,
               verbosity: int = VerbosityEnum.INFO,
               edge_bins: int = 1,
               highres_bin_size_minutes: int = 5,
               keep_highres_bydatetime: bool = False,
               nonstationary_stats: bool = True,
               stationary_stats: bool = True,
               ) -> Dict:
    """
    Compute occupancy, arrival, and departure statistics by category, time bin of day and day of week.

    Main function that first calls `bydatetime.make_bydatetime` to calculate occupancy, arrival
    and departure values by date by time bin and then calls `summarize.summarize`
    to compute the summary statistics.

    Parameters
    ----------

    plot_export_path
    first_dow
    legend_properties
    subtitle_properties
    subtitle
    main_title_properties
    main_title
    cap_color
    pctile_linewidth
    pctile_linestyle
    pctile_color
    plot_percentiles
    bar_color_mean
    figsize
    plot_style
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
    cap : int, optional
        Capacity of area being analyzed, default is None
    export_bydatetime_csv : bool, optional
       If True, bydatetime DataFrames are exported to csv files. Default is True.
    export_summaries_csv : bool, optional
       If True, summary DataFrames are exported to csv files. Default is True.
    make_all_dow_plots : bool, optional
       If True, day of week plots are created for occupancy, arrival, and departure. Default is True.
    make_all_week_plots : bool, optional
       If True, full week plots are created for occupancy, arrival, and departure. Default is True.
    export_dow_plot : bool, optional
       If True, day of week plots are exported for occupancy, arrival, and departure. Default is True.
    export_week_plot : bool, optional
       If True, full week plots are exported for occupancy, arrival, and departure. Default is True.
    xlabel : str
        x-axis label, default='Hour'
    ylabel : str
        y-axis label, default='Patients'
    csv_export_path : str or Path, optional
        Destination path for exported csv and png files, default is current directory
    verbosity : int, optional
        Used to set level in loggers. 0=logging.WARNING (default=0), 1=logging.INFO, 2=logging.DEBUG
    los_units : str, optional
        The time units to length of stay analysis.
        See https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.html for allowable values (smallest
        value allowed is 'seconds', largest is 'days'. The default is 'hours'.
    edge_bins: int, default 1
        Occupancy contribution method for arrival and departure bins. 1=fractional, 2=whole bin
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


    Returns
    -------
    dict of DataFrames and plots
       The bydatetime DataFrames, all summary DataFrames and any plots created.
    """

    # Create scenario instance so that validation and preprocessing get done
    scenario = Scenario(scenario_name=scenario_name, stops_df=stops_df,
                        in_field=in_field, out_field=out_field,
                        start_analysis_dt=start_analysis_dt, end_analysis_dt=end_analysis_dt,
                        cat_field=cat_field,
                        bin_size_minutes=bin_size_minutes,
                        cats_to_exclude=cats_to_exclude, occ_weight_field=occ_weight_field,
                        edge_bins=edge_bins,
                        percentiles=percentiles, los_units=los_units,
                        csv_export_path=csv_export_path,
                        cap=cap,
                        make_all_dow_plots=make_all_dow_plots, make_all_week_plots=make_all_week_plots,
                        export_bydatetime_csv=export_bydatetime_csv,
                        export_summaries_csv=export_summaries_csv,
                        export_all_dow_plots=export_dow_plot,
                        export_all_week_plots=export_week_plot,
                        cap_color=cap_color,
                        plot_style=plot_style,
                        figsize=figsize,
                        bar_color_mean=bar_color_mean,
                        plot_percentiles=plot_percentiles,
                        pctile_color=pctile_color,
                        pctile_linestyle=pctile_linestyle,
                        pctile_linewidth=pctile_linewidth,
                        main_title=main_title,
                        main_title_properties=main_title_properties,
                        subtitle=subtitle,
                        subtitle_properties=subtitle_properties,
                        legend_properties=legend_properties,
                        xlabel=xlabel,
                        ylabel=ylabel,
                        first_dow=first_dow,
                        plot_export_path=plot_export_path,
                        highres_bin_size_minutes=highres_bin_size_minutes,
                        keep_highres_bydatetime=keep_highres_bydatetime,
                        stationary_stats=stationary_stats, nonstationary_stats=nonstationary_stats,
                        verbosity=verbosity)

    hills = _make_hills(scenario)
    return hills
