"""Hillmaker"""

# Authors: Mark Isken <isken@oakland.edu>
# License: BSD 3 clause

import pandas as pd

import bydatetime
import summarize


def hillmaker(scenario_name, stops_df, infield, outfield,
              start_analysis, end_analysis,
              catfield='',
              total_str='Total',
              bin_size_minutes=60,
              cat_to_exclude=[],
              totals=True,
              return_data=True,
              export_csv=True,
              export_path=''):


    """
    Compute occupancy, arrival, and departure statistics by time bin of day and day of week.

    Main function that first calls `bydatetime.make_bydatetime` to calculate occupancy, arrival
    and departure values by date by time bin and then calls `summarize.summarize_bydatetime`
    to compute the summary statistics.

    Parameters
    ----------
    scenario_name: string
        used in output filenames
    stops_df: DataFrame
        base data containing one row per visit
    infield: string
        column name corresponding to the arrival times
    outfield: string
        column name corresponding to the departure times
    start_analysis: datetime-like, str
        starting datetime for the analysis (must be convertible to pandas Timestamp)
    end_analysis: datetime-like, str
        ending datetime for the analysis (must be convertible to pandas Timestamp)
    catfield: string, default ''
        column name corresponding to the category. If none is specified, then only overall occupancy is analyzed.
    total_str: string, default 'Total'
        column name to use for the overall category
    bin_size_minutes: int, default 60
        number of minutes in each time bin of the day
    cat_to_exclude: list, default []

    """

    # Create the bydatetime dataframe
    bydt_df = bydatetime.make_bydatetime(stops_df,
                                         infield,
                                         outfield,
                                         start_analysis,
                                         end_analysis,
                                         catfield,
                                         total_str,
                                         bin_size_minutes,
                                         cat_to_exclude=cat_to_exclude,
                                         totals=totals)

    # Create the summary stats DataFrames
    occ_stats_summary, arr_stats_summary, dep_stats_summary = summarize.summarize_bydatetime(bydt_df)
    occ_stats_summary_cat, arr_stats_summary_cat, dep_stats_summary_cat = summarize.summarize_category(bydt_df)

    # Export results to csv if requested
    if export_csv:

        # Output the files in csv format
        file_bydt_csv = export_path + '/bydatetime_' + scenario_name + '.csv'

        file_occ_csv = export_path + '/occ_stats_summary_' + scenario_name + '.csv'
        file_arr_csv = export_path + '/arr_stats_summary_' + scenario_name + '.csv'
        file_dep_csv = export_path + '/dep_stats_summary_' + scenario_name + '.csv'

        file_occ_cat_csv = export_path + '/occ_stats_summary_cat_' + scenario_name + '.csv'
        file_arr_cat_csv = export_path + '/arr_stats_summary_cat_' + scenario_name + '.csv'
        file_dep_cat_csv = export_path + '/dep_stats_summary_cat_' + scenario_name + '.csv'

        dt_cols = ['category', 'datetime', 'arrivals', 'departures', 'occupancy']
        bydt_df.to_csv(file_bydt_csv, index=False, float_format='%.6f', columns=dt_cols)

        summary_cols = ['category', 'day_of_week', 'bin_of_day',
                        'count', 'mean', 'stdev', 'sem', 'cv',
                        'var', 'skew', 'kurt',
                        'p50', 'p55', 'p60', 'p65', 'p70', 'p75',
                        'p80', 'p85', 'p90', 'p95', 'p975', 'p99']

        occ_stats_summary.to_csv(file_occ_csv, float_format='%.6f', columns=summary_cols)
        arr_stats_summary.to_csv(file_arr_csv, float_format='%.6f', columns=summary_cols)
        dep_stats_summary.to_csv(file_dep_csv, float_format='%.6f', columns=summary_cols)

        occ_stats_summary_cat.to_csv(file_occ_cat_csv, float_format='%.6f', columns=summary_cols)
        arr_stats_summary_cat.to_csv(file_arr_cat_csv, float_format='%.6f', columns=summary_cols)
        dep_stats_summary_cat.to_csv(file_dep_cat_csv, float_format='%.6f', columns=summary_cols)

    # Return data frames if requested
    if return_data:
        summaries = {'bydatetime': bydt_df,
                     'occupancy': occ_stats_summary,
                     'arrivals': arr_stats_summary,
                     'departures': dep_stats_summary,
                     'tot_occ': occ_stats_summary_cat,
                     'tot_arr': arr_stats_summary_cat,
                     'tot_dep': dep_stats_summary_cat}

        return summaries


if __name__ == '__main__':

    file_stopdata = 'data/ShortStay.csv'

    # Required inputs
    scenario = 'sstest_60'
    in_fld_name = 'InRoomTS'
    out_fld_name = 'OutRoomTS'
    cat_fld_name = 'PatType'
    start = '1/1/1996'
    end = '3/30/1996 23:45'

    # Optional inputs
    tot_fld_name = 'SSU'
    bin_mins = 60
    whichcats = ['ART', 'IVT']

    df = pd.read_csv(file_stopdata,parse_dates=[in_fld_name, out_fld_name])

    hillmaker(scenario, df, in_fld_name, out_fld_name,
              start, end, cat_fld_name,
              tot_fld_name, bin_mins,
              cat_to_exclude=whichcats,
              export_path='./testing')

