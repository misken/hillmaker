import pandas as pd
from hillmaker.hmlib import *

file_stopdata = '../data/ShortStay2_10pct.csv'
stops_df = pd.read_csv(file_stopdata, parse_dates=['InRoomTS','OutRoomTS'])
stops_df.info() # Check out the structure of the resulting DataFrame

infield = 'InRoomTS'
outfield = 'OutRoomTS'
catfield = 'PatType'

for row in stops_df.iterrows():
    intime_raw = row[1][infield]
    outtime_raw = row[1][outfield]

    catseries = row[1][catfield]
    cat = tuple(catseries)

    intime = to_the_second(intime_raw)
    outtime = to_the_second(outtime_raw)