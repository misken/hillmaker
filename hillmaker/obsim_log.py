__author__ = 'mark'

import pandas as pd
from pandas import Timestamp

import hillmaker as hm



file_stopdata = 'data/unit_stop_log_Experiment1_Scenario1_Rep1.csv'

scenario_name = 'log_unitocc_test'
in_fld_name = 'EnteredTS'
out_fld_name = 'ExitedTS'
cat_fld_name = 'Unit'
start_analysis = '3/24/2015 00:00'
end_analysis = '6/16/2016 00:00'

# Optional inputs

tot_fld_name = 'OBTot'
bin_size_mins = 1440
includecats = ['LDR','PP']

df = pd.read_csv(file_stopdata)
basedate = Timestamp('20150215 00:00:00')
df['EnteredTS'] = df.apply(lambda row:
                           Timestamp(round((basedate + pd.DateOffset(hours=row['Entered'])).value,-9)), axis=1)

df['ExitedTS'] = df.apply(lambda row:
                          Timestamp(round((basedate + pd.DateOffset(hours=row['Exited'])).value,-9)), axis=1)

hm.run_hillmaker(scenario_name,df,in_fld_name, out_fld_name,cat_fld_name,
                                     start_analysis,end_analysis,
                                     tot_fld_name,bin_size_mins,
                                     categories=includecats,
                                     outputpath='./testing')








