__author__ = 'isken'

import hmlib as hillpy

class Scenario:
    """
    Encapsulates all inputs needed to run a hillmaker scenario.

    Parameters
    ----------
    D : data source
       Stop data

    infield : string
       Name of column in D to use as arrival datetime

    outfield : string
       Name of column in D to use as departure datetime

    catfield : string
       Name of column in D to use as category field

    total_str : string
       Value to use for the totals

    bin_size_mins : int
       Bin size in minutes. Should divide evenly into 1440.
    """

    def __init__(self):
        file = open("stopwords.txt","r")
        self.excludes = set(line.strip() for line in file)
        file.close()
        self.docid = 0



