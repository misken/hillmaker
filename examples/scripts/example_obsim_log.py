import pandas as pd

import hillmaker as hm

# Read input data into DataFrame
file_stopdata = '../data/unit_stop_log.csv'
df = pd.read_csv(file_stopdata)

# Convert simulation clock times to pandas Timestamps as offsets from a base datetime
basedate = pd.Timestamp('20150215 00:00:00')

df['EnteredTS'] = df.apply(lambda row:
                           pd.Timestamp(round((basedate + pd.DateOffset(hours=row['Entered'])).value, -9)), axis=1)

df['ExitedTS'] = df.apply(lambda row:
                           pd.Timestamp(round((basedate + pd.DateOffset(hours=row['Exited'])).value,-9)), axis=1)
                           
scenario_name = 'log_unitocc_test'
in_fld_name = 'EnteredTS'
out_fld_name = 'ExitedTS'
cat_fld_name = 'Unit'
start_analysis = '4/1/2015'
end_analysis = '11/1/2017'

# Optional inputs
bin_size_mins = 120
output_path = './output'

results = hm.make_hills(scenario_name, df, in_fld_name, out_fld_name,
                        start_analysis, end_analysis, cat_fld_name,
                        bin_size_minutes=bin_size_mins,
                        csv_export_path=output_path, verbose=1)

print(results.keys())
