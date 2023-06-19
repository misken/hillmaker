import pandas as pd
from pandas import Timestamp

import hillmaker

file_stopdata = '../examples/data/unit_stop_log_Experiment1_Scenario138_Rep17.csv'

scenario_name = 'log_unitocc_test_5'
in_fld_name = 'EnteredTS'
out_fld_name = 'ExitedTS'
cat_fld_name = 'Unit'
start_analysis = '12/12/2015 00:00'
end_analysis = '12/19/2021 00:00'
# Optional inputs

tot_fld_name = 'OBTot'
bin_size_mins = 5
excludecats = ['Obs']

df = pd.read_csv(file_stopdata)
basedate = Timestamp('20150215 00:00:00')
df['EnteredTS'] = df.apply(lambda row:
                           Timestamp(round((basedate + pd.DateOffset(hours=row['Entered'])).value, -9)), axis=1)

df['ExitedTS'] = df.apply(lambda row:
                           Timestamp(round((basedate + pd.DateOffset(hours=row['Exited'])).value,-9)), axis=1)

# Filter input data by included included categories

df = df[df[cat_fld_name].isin(excludecats) == False]

hillmaker.make_hills(scenario_name, df, in_fld_name, out_fld_name,
                     start_analysis, end_analysis, cat_fld_name,
                     total_str=tot_fld_name, bin_size_minutes=bin_size_mins,
                     nonstationary_stats=False,
                     output_path='.',
                     cats_to_exclude=excludecats, verbose=1)
