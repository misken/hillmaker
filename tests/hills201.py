import pandas as pd

import hillmaker as hm

stops_df = pd.read_csv('fixtures/ShortStay2_10pct.csv', parse_dates=['InRoomTS', 'OutRoomTS'])

# Required inputs
in_field_name = 'InRoomTS'
out_field_name = 'OutRoomTS'
start_date = '1996-01-01'
end_date = pd.Timestamp('9/30/1996')

# Optional inputs
scenario_name = 'ss_example_1'
cat_field_name = 'PatType'
verbosity = 1 # INFO level logging
output_path = './output'
bin_size_minutes = 60

scenario01 = hm.HillsScenario(stops_df = stops_df,
                              in_field = in_field_name, out_field = out_field_name,
                              start_analysis_dt = start_date, end_analysis_dt = end_date,
                              cat_field = cat_field_name)


scenario_dict = scenario01.scenario_params.dict()
print(scenario_dict)

scenario01.make_hills()
print(scenario01.hills.keys())