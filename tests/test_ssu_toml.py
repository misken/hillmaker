from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import hillmaker as hm

config_path = Path('./fixtures/ssu_demo.toml')

# with open(config_path, "rb") as f:
#     params_toml_dict = tomllib.load(f)
# print(params_toml_dict)

# hills = hm.make_hills(config=config_path)
scenario = hm.create_scenario(config_path=config_path)

scenario.make_hills()

print(scenario.hills.keys())
print(scenario.hills['plots'].keys())

assert scenario.legend_properties is not None



