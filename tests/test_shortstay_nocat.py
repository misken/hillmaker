

import pandas as pd

import hillmaker as hm

file_stopdata = './fixtures/ShortStay2_10pct.csv'

# Required inputs
scenario_name = 'ss_example_1'
in_field_name = 'InRoomTS'
out_field_name = 'OutRoomTS'
start_date = '1996-01-01'
end_date = pd.Timestamp('3/30/1996')

# Optional inputs

cat_field_name = 'PatType'
verbosity = 1  # INFO level logging
output_path = './output'
bin_size_minutes = 60


df = pd.read_csv(file_stopdata, parse_dates=[in_field_name, out_field_name])

hm.make_hills(scenario_name=scenario_name, stops_df=df,
              in_field=in_field_name, out_field=out_field_name,
              start_analysis_dt=start_date, end_analysis_dt=end_date,
              bin_size_minutes=bin_size_minutes,
              csv_export_path='./output', verbosity=verbosity,
              export_summaries_csv=True)

