import pandas as pd
from math import isclose

from hillmaker.scenario import create_scenario


def test_inner_onebin_lrfrac():
    # Create test case

    scenario_name = 'inner_onebin_lrfrac'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 7:05'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 7:22')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['occupancy'], 17 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 17 / 30)


def test_inner_onebin_boundary():
    # Create test case

    scenario_name = 'inner_onebin_boundary'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 7:00'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 7:30')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['occupancy'], 30 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 30 / 30)


def test_inner_twobins_lrfrac():
    # Create test case

    scenario_name = 'inner_twobins_lrfrac'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 7:20'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 7:50')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['occupancy'], 10 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['occupancy'], 20 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 30 / 30)


def test_inner_twobins_lfrac():
    # Create test case

    scenario_name = 'inner_twobins_lfrac'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 7:00'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 7:50')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['occupancy'], 20 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 50 / 30)


def test_inner_twobins_rfrac():
    # Create test case

    scenario_name = 'inner_twobins_rfrac'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 7:20'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 8:00')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 8:00')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['occupancy'], 10 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['occupancy'], 30 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 40 / 30)


def test_inner_twobins_boundary():
    # Create test case

    scenario_name = 'inner_twobins_boundary'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 7:00'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 8:00')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 8:00')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['occupancy'], 30 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 60 / 30)


def test_inner_mbins_lrfrac():
    # Create test case
    # 1/1/2024 7:20,1/1/2024 8:50,inner_mbins_frac

    scenario_name = 'inner_mbins_lrfrac'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 7:20'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 8:50')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 8:30')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['occupancy'], 10 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 8:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 8:30')]['occupancy'], 20 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 90 / 30)


def test_inner_mbins_lfrac():
    # Create test case

    scenario_name = 'inner_mbins_lrfrac'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 7:20'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 9:30')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 9:30')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['occupancy'], 10 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 8:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 8:30')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 9:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 9:30')]['occupancy'], 0 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 130 / 30)


def test_inner_mbins_rfrac():
    # Create test case

    scenario_name = 'inner_mbins_lrfrac'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 7:00'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 9:20')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 9:00')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 8:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 8:30')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 9:00')]['occupancy'], 20 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 140 / 30)


def test_inner_mbins_boundary():
    # Create test case

    scenario_name = 'inner_mbins_boundary'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 7:00'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 9:00')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 9:00')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 8:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 8:30')]['occupancy'], 30 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 120 / 30)


def test_inner_mbins_lrfrac_overmid():
    # Create test case

    scenario_name = 'inner_mbins_lrfrac_overmid'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-02')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 23:20'),
                   'OutRoomTS': pd.Timestamp('2024-01-02 1:50')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 23:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-02 1:30')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 23:00')]['occupancy'], 10 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 23:30')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-02 0:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-02 0:30')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-02 1:00')]['occupancy'], 30 / 30)
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-02 1:30')]['occupancy'], 20 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), 150 / 30)


def test_left_mbins_rfrac():
    # Create test case

    scenario_name = 'test_left_mbins_rfrac'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2023-12-31 10:20'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 8:50')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df['arrivals'].sum() == 0.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 8:30')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    occ_series = pd.Series(
        bydatetime_df.loc[pd.Timestamp('2024-01-01 0:00'):pd.Timestamp('2024-01-01 8:00')]['occupancy'])
    occ_series.reset_index(inplace=True, drop=True)
    assert occ_series.equals(
        pd.Series([1.0] * len(occ_series)))
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 8:30')]['occupancy'], 20 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), (len(occ_series) * 30 + 20) / 30)


def test_left_mbins_boundary():
    # Create test case

    scenario_name = 'test_left_mbins_boundary'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2023-12-31 10:20'),
                   'OutRoomTS': pd.Timestamp('2024-01-01 8:30')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df['arrivals'].sum() == 0.0

    # Departure bin and total number of departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 8:30')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 1.0

    # Occupancy in relevant bins and total occupancy
    occ_series = pd.Series(
        bydatetime_df.loc[pd.Timestamp('2024-01-01 0:00'):pd.Timestamp('2024-01-01 8:00')]['occupancy'])
    occ_series.reset_index(inplace=True, drop=True)
    assert occ_series.equals(
        pd.Series([1.0] * len(occ_series)))

    assert isclose(bydatetime_df['occupancy'].sum(), (len(occ_series) * 30) / 30)


def test_right_mbins_lfrac():
    # Create test case

    scenario_name = 'test_right_mbins_lfrac'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 23:20'),
                   'OutRoomTS': pd.Timestamp('2024-02-01 8:50')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 23:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df['departures'].sum() == 0.0

    # Occupancy in relevant bins and total occupancy
    occ_series = pd.Series(
        bydatetime_df.loc[pd.Timestamp('2024-01-01 23:30'):pd.Timestamp('2024-01-01 23:30')]['occupancy'])
    occ_series.reset_index(inplace=True, drop=True)
    assert occ_series.equals(
        pd.Series([1.0] * len(occ_series)))
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 23:00')]['occupancy'], 10 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), (len(occ_series) * 30 + 10) / 30)


def test_right_mbins_boundary():
    # Create test case

    scenario_name = 'test_right_mbins_boundary'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2024-01-01 23:20'),
                   'OutRoomTS': pd.Timestamp('2024-02-01 8:30')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 23:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 1.0

    # Departure bin and total number of departures
    assert bydatetime_df['departures'].sum() == 0.0

    # Occupancy in relevant bins and total occupancy
    occ_series = pd.Series(
        bydatetime_df.loc[pd.Timestamp('2024-01-01 23:30'):pd.Timestamp('2024-01-01 23:30')]['occupancy'])
    occ_series.reset_index(inplace=True, drop=True)
    assert occ_series.equals(
        pd.Series([1.0] * len(occ_series)))
    assert isclose(bydatetime_df.loc[pd.Timestamp('2024-01-01 23:00')]['occupancy'], 10 / 30)

    assert isclose(bydatetime_df['occupancy'].sum(), (len(occ_series) * 30 + 10) / 30)


def test_outer_mbins_boundary():
    # Create test case

    scenario_name = 'test_outer_mbins_boundary'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_record = {'InRoomTS': pd.Timestamp('2023-12-31 11:20'),
                   'OutRoomTS': pd.Timestamp('2024-02-01 8:50')}

    stops_df = pd.DataFrame({k: [v] for k, v in stop_record.items()})

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Check results

    # Arrival bin and total number of arrivals
    assert bydatetime_df['arrivals'].sum() == 0.0

    # Departure bin and total number of departures
    assert bydatetime_df['departures'].sum() == 0.0

    # Occupancy in relevant bins and total occupancy
    occ_series = pd.Series(
        bydatetime_df.loc[pd.Timestamp('2024-01-01 0:00'):pd.Timestamp('2024-01-01 23:30')]['occupancy'])
    occ_series.reset_index(inplace=True, drop=True)
    assert occ_series.equals(
        pd.Series([1.0] * len(occ_series)))

    assert isclose(bydatetime_df['occupancy'].sum(), (len(occ_series) * 30) / 30)


def test_occ_multiple_recs():

    scenario_name = 'multiple_stop_recs'
    bin_size_minutes = 30
    start_analysis_dt = pd.Timestamp('2024-01-01')
    end_analysis_dt = pd.Timestamp('2024-01-01')
    stop_records = [{'InRoomTS': pd.Timestamp('2023-12-31 11:20'),
                     'OutRoomTS': pd.Timestamp('2024-02-01 8:50'),
                     'type': 'outer'},
                    {'InRoomTS': pd.Timestamp('2024-01-01 7:20'),
                     'OutRoomTS': pd.Timestamp('2024-01-01 8:50'),
                     'type': 'inner'},
                    {'InRoomTS': pd.Timestamp('2024-01-01 23:20'),
                     'OutRoomTS': pd.Timestamp('2024-02-01 8:30'),
                     'type': 'right'},
                    {'InRoomTS': pd.Timestamp('2023-12-31 10:20'),
                     'OutRoomTS': pd.Timestamp('2024-01-01 7:50'),
                     'type': 'left'}
                    ]

    stops_df = pd.DataFrame(stop_records)
    print(stops_df)

    scenario_params = {'scenario_name': scenario_name,
                       'data': stops_df,
                       'in_field': 'InRoomTS', 'out_field': 'OutRoomTS',
                       'start_analysis_dt': start_analysis_dt,
                       'end_analysis_dt': end_analysis_dt,
                       'bin_size_minutes': bin_size_minutes}

    # Create scenario and run hillmaker
    scenario = create_scenario(scenario_params)
    scenario.compute_hills_stats()
    bydatetime_df = scenario.get_bydatetime_df(by_category=False)

    # Arrivals
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:00')]['arrivals'] == 1.0
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 23:00')]['arrivals'] == 1.0
    assert bydatetime_df['arrivals'].sum() == 2.0

    # Departures
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 7:30')]['departures'] == 1.0
    assert bydatetime_df.loc[pd.Timestamp('2024-01-01 8:30')]['departures'] == 1.0
    assert bydatetime_df['departures'].sum() == 2.0

    # Occupancy

    # outer
    outer_occ_series = pd.Series([1.0] * len(bydatetime_df))

    # left
    left_occ_series = pd.Series([0.0] * len(bydatetime_df))
    for i in range(15):
        left_occ_series[i] += 1.0
    left_occ_series[15] += 20 / 30

    # right
    right_occ_series = pd.Series([0.0] * len(bydatetime_df))
    right_occ_series[46] += 10 / 30
    right_occ_series[47] += 30 / 30

    # inner
    inner_occ_series = pd.Series([0.0] * len(bydatetime_df))
    inner_occ_series[14] += 10 / 30
    inner_occ_series[15] += 30 / 30
    inner_occ_series[16] += 30 / 30
    inner_occ_series[17] += 20 / 30

    total_occ_series = pd.Series(outer_occ_series + left_occ_series + right_occ_series + inner_occ_series)

    occ_series = pd.Series(
        bydatetime_df.loc[pd.Timestamp('2024-01-01 0:00'):pd.Timestamp('2024-01-01 23:30')]['occupancy'])
    occ_series.reset_index(inplace=True, drop=True)

    pd.testing.assert_series_equal(occ_series, total_occ_series, check_names=False)



