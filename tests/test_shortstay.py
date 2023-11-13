import pandas as pd

import hillmaker as hm
from hillmaker.scenario import create_scenario


def test_shortstay():
    file_stopdata = 'tests/fixtures/ssu_2024.csv'

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
    csv_export_path = 'tests/output'
    plot_export_path = 'tests/output'

    # Use legacy function interface
    hills = hm.make_hills(scenario_name=scenario_name, data=file_stopdata,
                          in_field=in_field_name, out_field=out_field_name,
                          start_analysis_dt=start_date, end_analysis_dt=end_date,
                          cat_field=cat_field_name,
                          bin_size_minutes=bin_size_minutes,
                          csv_export_path=csv_export_path, verbosity=verbosity,
                          export_summaries_csv=True,
                          make_all_dow_plots=make_all_dow_plots, plot_export_path=plot_export_path)

    hills_config = hm.make_hills(config='tests/fixtures/ssu_example_1_config.toml')

    scenario_1 = create_scenario(config_path='tests/fixtures/ssu_example_1_config.toml')
    scenario_1.make_hills()

    bydatetime = hm.get_bydatetime_df(hills)
    bydatetime_config = hm.get_bydatetime_df(hills_config)
    bydatetime_scenario_config = scenario_1.get_bydatetime_df()
    summary_df = hm.get_summary_df(hills, by_category=False)

    # bydatetime, bydatetime_config, and bydatetime_scenario_config should be equivalent
    pd.testing.assert_frame_equal(bydatetime, bydatetime_config)
    pd.testing.assert_frame_equal(bydatetime, bydatetime_scenario_config)

    # Now rerun with no catfield
    scenario_name = 'ss_example_1_nocat'

    hills_nocat = hm.make_hills(scenario_name=scenario_name, data=file_stopdata,
                                in_field=in_field_name, out_field=out_field_name,
                                start_analysis_dt=start_date, end_analysis_dt=end_date,
                                cat_field=None,
                                bin_size_minutes=bin_size_minutes,
                                csv_export_path=csv_export_path, verbosity=verbosity,
                                export_summaries_csv=True,
                                make_all_dow_plots=make_all_dow_plots, plot_export_path=plot_export_path)

    bydatetime_nocat = hm.get_bydatetime_df(hills_nocat)
    bydatetime_total = hm.get_bydatetime_df(hills, by_category=False)
    summary_nocat_df = hm.get_summary_df(hills_nocat, by_category=False)

    # summary and datetime for totals from catfield='PatType' should equal those from running with no catfield
    pd.testing.assert_frame_equal(summary_nocat_df, summary_df)
    pd.testing.assert_frame_equal(bydatetime_nocat, bydatetime_total)

    # keys in output hills type dataframes should all be equal
    assert [k for k in hills.keys()] == [k for k in hills_config.keys()]
    assert [k for k in hills.keys()] == [k for k in scenario_1.hills.keys()]
    assert [k for k in hills.keys()] == [k for k in hills_nocat.keys()]

