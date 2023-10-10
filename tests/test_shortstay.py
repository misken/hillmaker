import pandas as pd

import hillmaker as hm

file_stopdata = './fixtures/ssu_2024.csv'

# Required inputs
scenario_name = 'ss_example_1'
in_field_name = 'InRoomTS'
out_field_name = 'OutRoomTS'
start_date = '2024-01-02'
end_date = pd.Timestamp('3/30/2024')

# Optional inputs

cat_field_name = 'PatType'
verbosity = 1  # INFO level logging
output_path = './output'
bin_size_minutes = 60
highres_bin_size_minutes = 60
keep_highres_datetime = False
edge_bins = 1

df = pd.read_csv(file_stopdata, parse_dates=[in_field_name, out_field_name])

# Use legacy function interface
hm.make_hills(scenario_name=scenario_name, stops_df=df,
              in_field=in_field_name, out_field=out_field_name,
              start_analysis_dt=start_date, end_analysis_dt=end_date,
              cat_field=cat_field_name,
              bin_size_minutes=bin_size_minutes,
              highres_bin_size_minutes=highres_bin_size_minutes,
              keep_highres_bydatetime=keep_highres_datetime,
              csv_export_path='./output', verbosity=verbosity,
              export_summaries_csv=True,
              edge_bins=edge_bins)
