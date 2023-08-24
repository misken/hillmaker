from pathlib import Path
from hillmaker.utils import create_scenario

config_file = Path('./fixtures/ssu_example_3.toml')
scenario_3 = create_scenario(toml_path=config_file)
print(scenario_3)



