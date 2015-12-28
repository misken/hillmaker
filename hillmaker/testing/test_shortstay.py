__author__ = 'mark'

import pandas as pd
from pandas import Timestamp

import hillmaker as hm

file_stopdata = 'data/ShortStay.csv'

# Required inputs
scenario_name = 'sstest_60_a'
in_fld_name = 'InRoomTS'
out_fld_name = 'OutRoomTS'
cat_fld_name = 'PatType'
start_analysis = '1/1/1996'
end_analysis = '3/30/1996 23:45'


# Optional inputs

# This next field wasn't in original Hillmaker. Use it to specify the name to use for the overall totals.
# At this point the totals actually aren't being calculated.
tot_fld_name = 'SSU'

bin_size_mins = 60

includecats = ['ART','IVT']

df = pd.read_csv(file_stopdata, parse_dates=[in_fld_name,out_fld_name])

hm.hillmaker(scenario_name,df,in_fld_name, out_fld_name,
                                     start_analysis,end_analysis,cat_fld_name,
                                     tot_fld_name,bin_size_mins,
                                     categories=False,
                                     outputpath='./testing')
