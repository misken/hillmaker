# Copyright 2022 Mark Isken, Jacob Norman

from datetime import datetime as dt
import os
import sys
import json
from gooey import Gooey, GooeyParser


@Gooey(program_name='Hillmaker Occupancy Analysis',
       target='hillmaker.exe',
       default_size=(610, 610),
       required_cols=2,
       optional_cols=2,
       tabbed_groups=True,
       use_events='VALIDATE_FORM'
       )
def get_user_input(argv=None):
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
    args_file = f'{script_name}-args.json'

    # read in the prior arguments as a dictionary
    if os.path.isfile(args_file):
        with open(args_file) as data_file:
            stored_args = json.load(data_file)

    test = "user_input.lower().endswith('.csv')"
    message = 'Must be .csv file'
    today = str(int(dt.now().strftime('%Y%m%d')))

    parser = GooeyParser(description='Computes occupancy statistics based on a list of start and stop times.')

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

    parser.add_argument('stop_data_csv',
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

    parser.add_argument('in_field',
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

    parser.add_argument('out_field',
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

    parser.add_argument('start_analysis_dt',
                        metavar='Start Date',
                        action='store',
                        default=stored_args.get('start_ts'),
                        help='Set the time out field name',
                        widget='DateChooser',
                        gooey_options={
                            'validator': {
                                'test': 'int(user_input.replace("-", "")) <= ' + today,
                                'message': 'Must be a valid date up to and including today'
                            }
                        })

    parser.add_argument('end_analysis_dt',
                        metavar='End Date',
                        action='store',
                        default=stored_args.get('end_ts'),
                        help='Set the time out field name',
                        widget='DateChooser',
                        gooey_options={
                            'validator': {
                                'test': 'int(user_input.replace("-", "")) <= ' + today,
                                'message': 'Must be a valid date up to and including today'
                            }
                        })

    parser.add_argument('--cat_field',
                        metavar='Category',
                        action='store',
                        #default=stored_args.get('cat_fld_name'),
                        help='Select a category to separate analysis by'
                        )

    parser.add_argument('--bin_size_mins',
                        metavar='Bin Size',
                        action='store',
                        widget='Slider',
                        default=60,
                        help='The size of the time bins in minutes',
                        type=int,
                        gooey_options={'min': 0, 'max': 60}
                        )

    parser.add_argument('--output_path',
                        metavar='Output Directory',
                        action='store',
                        widget='DirChooser',
                        default=stored_args.get('output_dir'),
                        help='Select output directory to save files',
                        )

    parser.add_argument('--verbosity',
                        metavar='Verbosity',
                        action='store',
                        widget='Slider',
                        default=0,
                        help='0=logging.WARNING, 1=logging.INFO, 2=logging.DEBUG',
                        type=int,
                        gooey_options={'min': 0, 'max': 2}
                        )

    args = parser.parse_args()
    # store the values of the args to be defaults on next run
    with open(args_file, 'w') as data_file:
        # using vars(args) returns the data as a dictionary
        json.dump({i: vars(args)[i] for i in vars(args) if i != 'db_pwd'}, data_file)
    return args


def main(argv=None):
    """
    :param argv: Input arguments
    :return: No return value
    """
    # launch gui and get user input
    inputs = get_user_input()


if __name__ == '__main__':
    sys.exit(main())
