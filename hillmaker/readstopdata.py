__author__ = 'isken'

import pickle
import pandas as pd
import time

if __name__ == '__main__':


    file_stopdata = 'data/ShortStay.csv'
    file_stopdata_pkl = 'data/ShortStay.pkl'

    in_fld_name = 'InRoomTS'
    out_fld_name = 'OutRoomTS'


    df = pd.read_csv(file_stopdata,parse_dates=[in_fld_name,out_fld_name])
    print ("CSV stop data file read: {}".format(time.clock()))

    # Following doesn't work for some reason
    # stopdb = open(file_stopdata_pkl,'w')
    # pickle.dump(df, stopdb)
    # stopdb.close()

    df.to_pickle(file_stopdata_pkl)

    print ("Pickled stop data file written: {}".format(time.clock()))

