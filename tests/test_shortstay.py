import pandas as pd

import hillmaker as hm
from hillmaker.scenario import create_scenario

file_stopdata = './fixtures/ssu_2024.csv'

# Required inputs
scenario_name = 'ss_example_1'
in_field_name = 'InRoomTS'
out_field_name = 'OutRoomTS'
start_date = '2024-01-02'
end_date = pd.Timestamp('3/30/2024')

# Optional inputs

make_all_dow_plots = False
cat_field_name = 'PatType'
verbosity = 1  # INFO level logging
bin_size_minutes = 60
csv_export_path = './output'
plot_export_path = './output'

# Use legacy function interface
hills = hm.make_hills(scenario_name=scenario_name, data=file_stopdata,
                      in_field=in_field_name, out_field=out_field_name,
                      start_analysis_dt=start_date, end_analysis_dt=end_date,
                      cat_field=cat_field_name,
                      bin_size_minutes=bin_size_minutes,
                      csv_export_path=csv_export_path, verbosity=verbosity,
                      export_summaries_csv=True,
                      make_all_dow_plots=make_all_dow_plots, plot_export_path=plot_export_path)

hills_config = hm.make_hills(config='fixtures/ssu_example_1_config.toml')

scenario_1 = create_scenario(config_path='fixtures/ssu_example_1_config.toml')
scenario_1.make_hills()

bydatetime = hm.get_bydatetime_df(hills)
bydatetime_config = hm.get_bydatetime_df(hills_config)
bydatetime_scenario_config = scenario_1.get_bydatetime_df()

print(hills.keys())
print(hills_config.keys())
print(scenario_1.hills.keys())

pd.testing.assert_frame_equal(bydatetime, bydatetime_config)
pd.testing.assert_frame_equal(bydatetime, bydatetime_scenario_config)



