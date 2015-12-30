import pandas as pd
from pandas import Timestamp

import hills

file_stopdata = 'data/unit_stop_log_Experiment1_Scenario1_Rep1.csv'

scenario_name = 'log_unitocc_test'
in_fld_name = 'EnteredTS'
out_fld_name = 'ExitedTS'
cat_fld_name = 'Unit'
start_analysis = '4/1/2015 00:00'
end_analysis = '11/1/2017 00:00'

# Optional inputs

tot_fld_name = 'OBTot'
bin_size_mins = 60
excludecats = ['Obs']

df = pd.read_csv(file_stopdata)
basedate = Timestamp('20150215 00:00:00')
df['EnteredTS'] = df.apply(lambda row:
                           Timestamp(round((basedate + pd.DateOffset(hours=row['Entered'])).value, -9)), axis=1)

df['ExitedTS'] = df.apply(lambda row:
                           Timestamp(round((basedate + pd.DateOffset(hours=row['Exited'])).value,-9)), axis=1)

# Filter input data by included included categories

df = df[df[cat_fld_name].isnotin(excludecats)]

hills.make_hills(scenario_name, df, in_fld_name, out_fld_name,
                 start_analysis, end_analysis, cat_fld_name,
                 total_str=tot_fld_name, bin_size_minutes=bin_size_mins,
                 export_path='./testing/output',
                 cat_to_exclude=excludecats, verbose=1)
