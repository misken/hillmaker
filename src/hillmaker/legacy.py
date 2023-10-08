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
               highres_bin_size_minutes: int = 5,
               keep_highres_bydatetime: bool = False,
               percentiles: Tuple | List = (0.25, 0.5, 0.75, 0.95, 0.99),
               cats_to_exclude: str | None = None,
               occ_weight_field: str | None = None,
               cap: int | None = None,
               nonstationary_stats: bool = True,
               stationary_stats: bool = True,
               export_bydatetime_csv: bool = True,
               export_summaries_csv: bool = True,
               make_all_dow_plots: bool = True,
               make_all_week_plots: bool = True,
               export_dow_plot: bool = True,
               export_week_plot: bool = True,
               xlabel: str | None = None,
               ylabel: str | None = None,
               output_path: str | Path = Path('.'),
               verbosity: int = VerbosityEnum.WARNING,
               los_units: str = 'hours') -> Dict:
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
    highres_bin_size_minutes : int, optional
        Number of minutes in each time bin of the day used for initial computation of the number of arrivals,
        departures, and the occupancy level. This value should be <= `bin_size_minutes`. The shorter the duration of
        stays, the smaller the resolution should be. The current default is 5 minutes.
    keep_highres_bydatetime : bool, optional
        Save the high resolution bydatetime dataframe in hills attribute. Default is False.
    percentiles : list or tuple of floats (e.g. [0.5, 0.75, 0.95]), optional
        Which percentiles to compute. Default is (0.25, 0.5, 0.75, 0.95, 0.99)
    cats_to_exclude : list, optional
        Category values to ignore, default is None
    occ_weight_field : str, optional
        Column name corresponding to the weights to use for occupancy incrementing, default is None
        which corresponds to a weight of 1.0.
    cap : int, optional
        Capacity of area being analyzed, default is None
    nonstationary_stats : bool, optional
       If True, datetime bin stats are computed. Else, they aren't computed. Default is True
    stationary_stats : bool, optional
       If True, overall, non-time bin dependent, stats are computed. Else, they aren't computed. Default is True
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
    output_path : str or Path, optional
        Destination path for exported csv and png files, default is current directory
    verbosity : int, optional
        Used to set level in loggers. 0=logging.WARNING (default=0), 1=logging.INFO, 2=logging.DEBUG
    los_units : str, optional
        The time units to length of stay analysis.
        See https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.html for allowable values (smallest
        value allowed is 'seconds', largest is 'days'). The default is 'hours'.


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
                        bin_size_minutes=bin_size_minutes, highres_bin_size_minutes=highres_bin_size_minutes,
                        keep_highres_bydatetime=keep_highres_bydatetime,
                        cats_to_exclude=cats_to_exclude, occ_weight_field=occ_weight_field,
                        stationary_stats=stationary_stats, nonstationary_stats=nonstationary_stats,
                        percentiles=percentiles, cap=cap,
                        make_all_dow_plots=make_all_dow_plots, make_all_week_plots=make_all_week_plots,
                        export_bydatetime_csv=export_bydatetime_csv,
                        export_summaries_csv=export_summaries_csv,
                        export_all_dow_plots=export_dow_plot,
                        export_all_week_plots=export_week_plot,
                        xlabel=xlabel, ylabel=ylabel,
                        output_path=output_path, verbosity=verbosity, los_units=los_units)

    hills = _make_hills(scenario)
    return hills

