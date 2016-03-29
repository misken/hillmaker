

import pandas as pd

import hillmaker as hm

file_stopdata = '../data/ShortStay2-mini.csv'

# Required inputs
scenario = 'sstest_60'
in_fld_name = 'InRoomTS'
out_fld_name = 'OutRoomTS'
#cat_fld_name = ['PatType','Severity']
#cat_fld_name = ['PatType']
cat_fld_name = None
start = '1/1/1996'
end = '1/10/1996 23:45'

# Optional inputs
#tot_fld_name = 'SSU'
bin_mins = 480


stops_df = pd.read_csv(file_stopdata, parse_dates=[in_fld_name, out_fld_name])

bydt_test_dfs = hm.bydatetime.make_bydatetime(stops_df, in_fld_name, out_fld_name,
                                          start, end,
                                         catfield=cat_fld_name, totals=2)

summaries_test_dfs = hm.summarize.summarize(bydt_test_dfs, nonstationary_stats=True, stationary_stats=True)

# hm.make_hills(scenario, stops_df, in_fld_name, out_fld_name,
#                      start, end, cat_fld_name,
#                      tot_fld_name, bin_mins,
#                      cat_to_exclude=None,
#                      export_path='./testing/output', verbose=1)

for d in bydt_test_dfs:
    print(bydt_test_dfs[d].head())
    file_bydt_csv = 'bydatetime_' + d + '.csv'
    bydt_test_dfs[d].to_csv(file_bydt_csv, index=False, float_format='%.6f')

#bydt_test_df.to_csv("bydt_test.csv",index=False)
