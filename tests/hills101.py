# https://python.plainenglish.io/pydantic-in-a-nutshell-63f1afa9ac8d
# https://towardsdatascience.com/how-to-make-the-most-of-pydantic-aa374d5c12d
# https://rednafi.github.io/digressions/python/2020/06/03/python-configs.html
# https://stefan.sofa-rockers.org/2020/05/29/attrs-dataclasses-pydantic/
# https://jackmckew.dev/dataclasses-vs-attrs-vs-pydantic.html
# https://mpkocher.github.io/2019/05/22/Dataclasses-in-Python-3-7/

from datetime import datetime, date
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, validator, BaseSettings, Field
from typing import Dict, List, Optional, Tuple, Union
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib



class Hills1(BaseModel):
    """pydantic model for hm inputs

    - using some required fields for now. So, can't, for example, create an instane with just a df
    and add the other "required" fields later. Still learning pydantic and couldn't figure out how to do well.
    - some of the defaults should live in some sort of settings file (see BaseSettings)

    """

    df: pd.DataFrame
    in_field: str
    out_field: str
    start_analysis_dt: Union[date, datetime]
    end_analysis_dt: Union[date, datetime]
    scenario: str = 'base'
    cat_field: str = None
    bin_size_minutes: int = 30
    percentiles: Union[Tuple[float], List[float]] = (0.5, 0.75, 0.95, 0.99)

    # Ensure fields exist
    @validator('in_field', 'out_field', 'cat_field')
    def field_exists(cls, v, values):
        if v not in values['df'].columns:
            raise ValueError(f'{v} is not a column in the dataframe')
        return v

    # End date >= start date
    @validator('end_analysis_dt')
    def date_relationship(cls, v, values):
        if v < values['start_analysis_dt']:
            raise ValueError(f'end date must be >= start date')
        return v

    # Ensure bin_size_minutes divides into 1440 with no remainder
    @validator('bin_size_minutes')
    def bin_size_minutes_divides(cls, v):
        if 1440 % v > 0:
            raise ValueError('bin_size_minutes must divide into 1440 with no remainder')
        return v

    class Config:
        arbitrary_types_allowed = True


class Settings(BaseSettings):
    # Default prefix to avoid collisions with environment variables
    class Config:
        env_prefix = "hillmaker_"

    # Application defaults
    default_bin_size_mins: int = 60
    default_percentiles: Union[Tuple[float], List[float]] = (0.25, 0.5, 0.75, 0.95, 0.99)

class Parameters(BaseModel):

    """pydantic model for hm input parameters

    """

    df: pd.DataFrame
    in_field: str
    out_field: str
    start_analysis_dt: Union[date, datetime]
    end_analysis_dt: Union[date, datetime]
    # Use default_factory to create dynamic default
    scenario: str = Field(default_factory=lambda : f's{datetime.now().strftime("%Y%m%d%H%M")}')
    cat_field: str = None
    bin_size_minutes: int = 60
    percentiles: Union[Tuple[float], List[float]] = (0.25, 0.5, 0.75, 0.95, 0.99)

    # Ensure fields exist
    @validator('in_field', 'out_field', 'cat_field')
    def field_exists(cls, v, values):
        if v not in values['df'].columns:
            raise ValueError(f'{v} is not a column in the dataframe')
        return v

    # End date >= start date
    @validator('end_analysis_dt')
    def date_relationship(cls, v, values):
        if v < values['start_analysis_dt']:
            raise ValueError(f'end date must be >= start date')
        return v

    # Ensure bin_size_minutes divides into 1440 with no remainder
    @validator('bin_size_minutes')
    def bin_size_minutes_divides(cls, v):
        if 1440 % v > 0:
            raise ValueError('bin_size_minutes must divide into 1440 with no remainder')
        return v

    class Config:
        arbitrary_types_allowed = True


class Hills2(BaseModel):
    """pydantic model for hm inputs

    - same as Hills1 except for
    - the default values for scenario, bin size, and percentiles live in a settings file

    """

    df: pd.DataFrame
    in_field: str
    out_field: str
    start_analysis_dt: Union[date, datetime]
    end_analysis_dt: Union[date, datetime]
    # Use default_factory to create dynamic default
    scenario: str = Field(default_factory=lambda : f's{datetime.now().strftime("%Y%m%d%H%M")}')
    cat_field: str = None
    bin_size_minutes: int = 60
    percentiles: Union[Tuple[float], List[float]] = (0.25, 0.5, 0.75, 0.95, 0.99)

    # Ensure fields exist
    @validator('in_field', 'out_field', 'cat_field')
    def field_exists(cls, v, values):
        if v not in values['df'].columns:
            raise ValueError(f'{v} is not a column in the dataframe')
        return v

    # End date >= start date
    @validator('end_analysis_dt')
    def date_relationship(cls, v, values):
        if v < values['start_analysis_dt']:
            raise ValueError(f'end date must be >= start date')
        return v

    # Ensure bin_size_minutes divides into 1440 with no remainder
    @validator('bin_size_minutes')
    def bin_size_minutes_divides(cls, v):
        if 1440 % v > 0:
            raise ValueError('bin_size_minutes must divide into 1440 with no remainder')
        return v

    class Config:
        arbitrary_types_allowed = True


class HillsScenario():
    """User facing class to gather inputs for a hillmaker scenario"""
    def __init__(
        self,
        params_dict: Optional[Dict] = None,
        params_path: Optional[Union[str, Path]] = None,
        **kwargs
    ):
        # Create empty dict for input parameters
        params = {}

        # If params_dict is not None, merge into params
        if params_dict is not None:
            params = params_dict.copy()

        # If params_path is not None, merge into params
        if params_path is not None:
            with open(params_path, mode="rb") as toml_file:
                params_toml = tomllib.load(toml_file)
            params = params | params_toml

        # Args passed to function get ultimate say
        if len(kwargs) > 0:
            params = params | kwargs

        # Now, from the params dictionary, create pydantic Parameters model
        # Be nice to construct model so that some of the default values
        # can be based on app settings
        # Get application settings
        # app_settings: Settings = Settings()

        params_model = Parameters(**params)
        self.scenario_params = params_model




ssu_df = pd.read_csv('fixtures/ShortStay2_10pct.csv', parse_dates=['InRoomTS', 'OutRoomTS'])
ssu_df['los_hrs'] = (ssu_df['OutRoomTS'] - ssu_df['InRoomTS']) / pd.Timedelta(1, 'h')
#print(ssu_df.head())

in_fld = 'InRoomTS'
out_fld = 'OutRoomTS'
start = '1996-01-01'
end = '1996-04-01'
cat_fld = 'PatType'


# Create new Hills instance

hm1 = Hills1(df=ssu_df, in_field=in_fld, out_field=out_fld,
            start_analysis_dt=start, end_analysis_dt=end,
            cat_field=cat_fld, bin_size_minutes=60)

hm2 = Hills1(df=ssu_df, in_field=in_fld, out_field=out_fld,
            start_analysis_dt='1996-02-01', end_analysis_dt=end,
            scenario='ssu2', cat_field=cat_fld, bin_size_minutes=30)

hm3 = Hills2(df=ssu_df, in_field=in_fld, out_field=out_fld,
            start_analysis_dt='1996-02-01', end_analysis_dt=end,
            cat_field=cat_fld, bin_size_minutes=30)

print(hm1.scenario, hm1.in_field, hm1.out_field, hm1.start_analysis_dt, hm1.bin_size_minutes)
print(hm2.scenario, hm2.in_field, hm2.out_field, hm2.start_analysis_dt, hm2.bin_size_minutes)
print(hm3.scenario, hm3.in_field, hm3.out_field, hm3.start_analysis_dt, hm3.bin_size_minutes)

hm4 = HillsScenario(df=ssu_df, in_field=in_fld, out_field=out_fld,
            start_analysis_dt=start, end_analysis_dt=end, scenario='hm4',
            cat_field=cat_fld, bin_size_minutes=60)


print(hm4.scenario_params.scenario, hm4.scenario_params.in_field, hm4.scenario_params.out_field,
      hm4.scenario_params.start_analysis_dt, hm4.scenario_params.bin_size_minutes)