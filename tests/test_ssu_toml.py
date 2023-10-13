from pathlib import Path
import hillmaker as hm

config_file = Path('./fixtures/ssu_example_3.toml')

hills = hm.make_hills(config=config_file)
#scenario_3 = create_scenario(toml_path=config_file)
print(hills.keys())
print(hills['plots'].keys())



