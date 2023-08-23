from typing import Dict, Optional
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import pandas as pd

from hillmaker import Scenario


def update_params_from_toml(params_dict, toml_dict):
    """
    Update dict of input parameters from toml_config dictionary

    Parameters
    ----------
    params_dict : dict
    toml_dict : dict from loading TOML config file

    Returns
    -------
    Updated parameters dict
    """

    # Flatten toml config (we know there are no key clashes and only one nesting level)
    # Update args dict from config dict
    for outerkey, outerval in toml_dict.items():
        for key, val in outerval.items():
            params_dict[key] = val

    return params_dict


def from_config(config: Path | str):
    scenario = Scenario.create_scenario(toml_path=config)
    return scenario


def from_dict(params_dict: dict):
    scenario = Scenario.create_scenario(params_dict=params_dict)
    return scenario


def create_scenario(params_dict: Optional[Dict] = None,
                    toml_path: Optional[str | Path] = None, **kwargs):
    """Function to create a `Scenario` from a dict, a TOML file, and/or keyword args """

    # Create empty dict for input parameters
    params = {}

    # If params_dict is not None, merge into params
    if params_dict is not None:
        params.update(params_dict)

    # If params_path is not None, merge into params
    if toml_path is not None:
        with open(toml_path, "rb") as f:
            params_toml_dict = tomllib.load(f)
            params = update_params_from_toml(params, params_toml_dict)

        # Read in stop data to DataFrame
        stops_df = pd.read_csv(params['stop_data_csv'], parse_dates=[params['in_field'], params['out_field']])
        params['stops_df'] = stops_df
        # Remove the csv key
        params.pop('stop_data_csv', None)

    # Args passed to function get ultimate say
    if len(kwargs) > 0:
        params.update(kwargs)

    # Now, from the params dictionary, create pydantic Parameters model
    # Be nice to construct model so that some default values
    # can be based on app settings
    # Get application settings
    # app_settings: Settings = Settings()

    # Create Pydantic model to parse and validate inputs
    scenario = Scenario(**params)
    return scenario
