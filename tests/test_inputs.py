import pandas as pd
from pydantic import ValidationError
import pytest

from hillmaker.scenario import create_scenario


def test_bad_analysis_date_range():
    file_stopdata = './tests/fixtures/ssu_2024.csv'

    # Required inputs
    scenario_name = 'ss_example_1'
    in_field_name = 'InRoomTS'
    out_field_name = 'OutRoomTS'
    start_analysis_dt = pd.Timestamp('2023-01-01')
    end_analysis_dt = pd.Timestamp('2023-03-30')

    # Optional inputs
    cat_field_name = 'PatType'
    bin_size_minutes = 60

    scenario_params = {'scenario_name': scenario_name,
                       'data': file_stopdata,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Analysis dates completely outside of data
    with pytest.raises(ValidationError) as e_info:
        scenario = create_scenario(scenario_params)

    # Start date > 48 hrs before first arrival
    scenario_params['start_analysis_dt'] = pd.Timestamp('2023-12-01')
    scenario_params['end_analysis_dt'] = pd.Timestamp('2024-12-01')
    with pytest.raises(ValidationError) as e_info:
        scenario = create_scenario(scenario_params)

    # End date > 48 hrs after last departure
    scenario_params['start_analysis_dt'] = pd.Timestamp('2024-01-01')
    scenario_params['end_analysis_dt'] = pd.Timestamp('2024-12-01')
    with pytest.raises(ValidationError) as e_info:
        scenario = create_scenario(scenario_params)
