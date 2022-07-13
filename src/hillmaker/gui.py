# Copyright 2022 Mark Isken, Jacob Norman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime as dt
import os
import json
from gooey import Gooey, GooeyParser
import pandas as pd
from hillmaker import make_hills


@Gooey(program_name='Hillmaker Occupancy Analysis',
       default_size=(610, 610),
       required_cols=2,
       optional_cols=2,
       tabbed_groups=True,
       use_events='VALIDATE_FORM'
       )
def get_user_input():
    """
    Adds GUI to hillmaker function make_hills.

    Use GooeyParser to get user-defined inputs for use with the
    hillmaker function make_hills. Saves the arguments in a
    default json file so that the most recent selections are the
    preselected values for subsequent runs.

    Returns
    ----------
    args : GooeyParser
        Used to retrieve user inputs.
    """

    stored_args = {}
    # get the script name without the extension and use it to build up
    # the json filename
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    args_file = "{}-args.json".format(script_name)

    # read in the prior arguments as a dictionary
    if os.path.isfile(args_file):
        with open(args_file) as data_file:
            stored_args = json.load(data_file)

    test = "user_input.lower().endswith('.csv')"
    message = 'Must be .csv file'

    parser = GooeyParser(description='Computes occupancy statistics based on a list of start and stop times.')
    parser.add_argument('stops_fn',
                        metavar='Timestamps Filename',
                        action='store',
                        default=stored_args.get('stops_fn'),
                        help='Select file containing start and stop times',
                        widget='FileChooser',
                        gooey_options={
                            'validator': {
                                'test': test,
                                'message': message
                            }
                        })

    parser.add_argument('scenario',
                        metavar='Scenario',
                        action='store',
                        default=stored_args.get('scenario'),
                        help='Specify a scenario name for output files',
                        gooey_options={
                            'validator': {
                                'test': 'len(user_input) > 0 ',
                                'message': 'Must be a valid year in integer form'
                            }
                        })

    parser.add_argument('in_fld_name',
                        metavar='In Time Field Name',
                        action='store',
                        default=stored_args.get('in_fld_name'),
                        help='Set the time in field name',
                        gooey_options={
                            'validator': {
                                'test': 'len(user_input) > 0 ',
                                'message': 'Must be a valid year in integer form'
                            }
                        })

    parser.add_argument('out_fld_name',
                        metavar='Out Time Field Name',
                        action='store',
                        default=stored_args.get('out_fld_name'),
                        help='Set the time out field name',
                        gooey_options={
                            'validator': {
                                'test': 'len(user_input) > 0 ',
                                'message': 'Must be a valid year in integer form'
                            }
                        })

    parser.add_argument('start_ts',
                        metavar='Start Date',
                        action='store',
                        default=stored_args.get('start_ts'),
                        help='Set the time out field name',
                        widget='DateChooser',
                        gooey_options={
                            'validator': {
                                'test': 'int(user_input.replace("-", "")) <= ' + str(int(dt.now().strftime('%Y%m%d'))),
                                'message': 'Must be a valid date up to and including today'
                            }
                        })

    parser.add_argument('end_ts',
                        metavar='End Date',
                        action='store',
                        default=stored_args.get('end_ts'),
                        help='Set the time out field name',
                        widget='DateChooser',
                        gooey_options={
                            'validator': {
                                'test': 'int(user_input.replace("-", "")) <= ' + str(int(dt.now().strftime('%Y%m%d'))),
                                'message': 'Must be a valid date up to and including today'
                            }
                        })

    parser.add_argument('-cat_fld_name', '-o',
                        metavar='Category',
                        action='store',
                        #default=stored_args.get('cat_fld_name'),
                        help='Select a category to separate analysis by'
                        )

    parser.add_argument('-bin_size',
                        metavar='Bin Size',
                        action='store',
                        widget='Slider',
                        default=60,
                        help='The size of the time bins in minutes',
                        type=int,
                        gooey_options={'min': 0, 'max': 60}
                        )

    parser.add_argument('-verbose',
                        metavar='Verbosity',
                        action='store',
                        widget='Slider',
                        default=0,
                        help='The higher the integer, the more verbose the output',
                        type=int,
                        gooey_options={'min': 0, 'max': 5}
                        )

    parser.add_argument('-output_dir',
                        metavar='Output Directory',
                        action='store',
                        widget='DirChooser',
                        default=stored_args.get('output_dir'),
                        help='Select output directory to save files',
                        )

    args = parser.parse_args()
    # store the values of the args to be defaults on next run
    with open(args_file, 'w') as data_file:
        # using vars(args) returns the data as a dictionary
        json.dump({i: vars(args)[i] for i in vars(args) if i != 'db_pwd'}, data_file)
    return args


def hill_gui():
    """
    Full program for computing occupancy based on in and out timestamps.

    Extends the functionality of hillmaker to include a graphic user
    interface with get_user_input to the function make_hills. Allows
    business users to easily run occupancy statistics and outputs files

    Returns
    -------
    hm_dict : dictionary
        Dictionary of hillmaker dataframes.
    """
    # launch gui and get user input
    inputs = get_user_input()

    # read in csv file and convert in and out cols to datetime
    stops_df = pd.read_csv(inputs.stops_fn, parse_dates=[inputs.in_fld_name, inputs.out_fld_name])

    # run occupancy analysis
    hm_dict = make_hills(inputs.scenario, stops_df, inputs.in_fld_name,
                         inputs.out_fld_name, inputs.start_ts, inputs.end_ts, cat_field=inputs.cat_fld_name,
                         bin_size_minutes=inputs.bin_size, export_path=inputs.output_dir, verbose=inputs.verbose)

    return hm_dict
