

import pandas as pd

import hillmaker as hm

file_stopdata = '../data/ShortStay2_10pct.csv'

# Required inputs
scenario = 'ShortStay2_10pct_120'
in_fld_name = 'InRoomTS'
out_fld_name = 'OutRoomTS'
#cat_fld_name = ['PatType','Severity']
cat_fld_name = ['PatType']
#cat_fld_name = None
start = '1/1/1996'
end = '3/30/1996 23:45'

# Optional inputs
#tot_fld_name = 'SSU'
bin_mins = 60


stops_df = pd.read_csv(file_stopdata, parse_dates=[in_fld_name, out_fld_name])

hills = hm.make_hills(scenario, stops_df, in_fld_name, out_fld_name,
                      start, end, cat_fld_name,
                      bin_mins,
                      cat_to_exclude=None,
                      nonstationary_stats=True,
                      stationary_stats=True,
                      export_bydatetimes_csv=True,
                      export_summaries_csv=True,
                      export_path='./output', verbose=1)

