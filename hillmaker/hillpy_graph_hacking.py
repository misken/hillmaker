# -*- coding: utf-8 -*-
"""
Created on Wed Jan 16 15:38:26 2013

@author: mark
"""

# General imports
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

# Pandas setup
from pandas import DataFrame, Series
import pandas as pd

from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse

# Change directory into working HillPy dir
# Change directory into working HillPy dir

    
occ_df = pd.read_csv('data/occ_stats_summary_sstest.csv')

tot_df = occ_df[occ_df['category']=='_Total']

occ_mean = tot_df['mean']
occ_95 = tot_df['p95']

occ_95.plot(kind='bar')

fig = plt.figure()  # Create Figure  to hold the plots
ax1 = fig.add_subplot(221)
ax2 = fig.add_subplot(222)
ax3 = fig.add_subplot(223)

ind = np.arange(168)    # the x locations for the groups

plt.ylabel('Occupancy')
plt.title('Short Stay Unit Total Occupancy')
#plt.xticks(ind+width/2., ('G1', 'G2', 'G3', 'G4', 'G5') )
#plt.yticks(np.arange(0,81,10))

plt.bar(ind,occ_mean) # Used this way (pyplot style), should add the bar
                  # chart to the most recent subplot instance
                  
# As opposed to pyplot based, can use the matplotlib api approach.
ax1.plot(occ_95)
ax1.bar(ind,occ_mean)
ax1.plot(tot_df['p55'], color='r')
plt.draw()  # Will redraw the screen

ax4 = fig.add_subplot(224)
ax4.plot(occ_mean, 'k--', label = 'mean occ')
ax4.plot(occ_95, 'k.', label = '95% occ')
ax4.legend(loc='best')

plt.draw()

# Figure 2 - A weekly Occupancy Graph
fig2 = plt.figure()  # Create Figure  to hold the plots
ax1 = fig2.add_subplot(111)
binofweek = np.arange(168)
ax1.bar(binofweek,occ_mean, color='#999966', linewidth=0, label = 'mean occ')
ax1.plot(occ_95, label = '95% occ')
ax1.legend(loc='best')

plt.ylabel('Occupancy')
plt.title('Short Stay Unit Total Occupancy')

majorLocator   = MultipleLocator(24)
majorFormatter = FormatStrFormatter('%d')
ax1.xaxis.set_major_locator(majorLocator)
ax1.xaxis.set_major_formatter(majorFormatter)
ax1.yaxis.grid(True, which='major')

plt.draw()