__author__ = 'mark'

import pandas as pd

import bydatetime
import summarize


def run_hillmaker(scenario_name,stops_df,infield,outfield,catfield,
                    start_analysis,end_analysis,
                    total_str='Total',
                    bin_size_minutes=60,
                    categories=False,
                    totals=True,
                    outputpath=''):

    # Create the bydatetime dataframe
    bydt_df = bydatetime.make_bydatetime(stops_df,
                                     infield,
                                     outfield,
                                     catfield,
                                     start_analysis,
                                     end_analysis,
                                     total_str,
                                     bin_size_minutes,
                                     categories=categories,
                                     totals=totals)

    # Create the summary stats dataframes
    occ_stats_summary,arr_stats_summary,dep_stats_summary = summarize.summarize_bydatetime(bydt_df)

    # Output the files in csv format
    file_bydt_csv = outputpath + '/bydatetime_' + scenario_name + '.csv'
    file_occ_csv = outputpath + '/occ_stats_summary_' + scenario_name + '.csv'
    file_arr_csv = outputpath + '/arr_stats_summary_' + scenario_name + '.csv'
    file_dep_csv = outputpath + '/dep_stats_summary_' + scenario_name + '.csv'

    bydt_df.to_csv(file_bydt_csv, index=False)
    occ_stats_summary.to_csv(file_occ_csv)
    arr_stats_summary.to_csv(file_arr_csv)
    dep_stats_summary.to_csv(file_dep_csv)







if __name__ == '__main__':

    file_stopdata = 'data/ShortStay.csv'

    # Required inputs
    scenario_name = 'sstest_60'
    in_fld_name = 'InRoomTS'
    out_fld_name = 'OutRoomTS'
    cat_fld_name = 'PatType'
    start_analysis = '1/1/1996'
    end_analysis = '3/30/1996 23:45'

    # Optional inputs
    tot_fld_name = 'SSU'
    bin_size_mins = 60
    includecats = ['ART','IVT']

    df = pd.read_csv(file_stopdata,parse_dates=[in_fld_name,out_fld_name])

    run_hillmaker(scenario_name,df,in_fld_name, out_fld_name,cat_fld_name,
                                     start_analysis,end_analysis,
                                     tot_fld_name,bin_size_mins,
                                     categories=includecats,
                                     outputpath='./testing')

