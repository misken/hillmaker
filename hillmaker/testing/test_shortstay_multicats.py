

import pandas as pd

import hillmaker as hm

file_stopdata = '../data/ShortStay3-mini.csv'

# Required inputs
scenario = 'sstest_60'
in_fld_name = 'InRoomTS'
out_fld_name = 'OutRoomTS'
cat_fld_name = ['PatType','Severity']
cat_fld_name = ['PatType']
cat_fld_name = None
start = '1/1/1996'
end = '3/30/1996 23:45'

# Optional inputs
tot_fld_name = 'SSU'
bin_mins = 60


stops_df = pd.read_csv(file_stopdata, parse_dates=[in_fld_name, out_fld_name])

bydt_test_df = hm.bydatetime.make_bydatetime(stops_df, in_fld_name, out_fld_name,
                                          start, end,
                                          catfield=cat_fld_name)

# hm.make_hills(scenario, stops_df, in_fld_name, out_fld_name,
#                      start, end, cat_fld_name,
#                      tot_fld_name, bin_mins,
#                      cat_to_exclude=None,
#                      export_path='./testing/output', verbose=1)

print(bydt_test_df.head())