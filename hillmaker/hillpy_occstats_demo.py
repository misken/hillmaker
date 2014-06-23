# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #Computing occupancy statistics with Python - Part 2 of 3#
# In the second part of this series, we will use Python to compute summary occupancy statistics (such as means and percentiles) by time of day, day of week, and patient category (recall that this example is from a hospital short stay unit - go back to Part 1 for all of the background info). Computation of percentiles by one or more grouping fields is a pain using tools like Excel, Access and SQL Server. With Python+pandas it's easy.

# <markdowncell>

# ##Preliminaries##

# <codecell>

import pandas as pd

# <markdowncell>

# At the end of Part 1 of this tutorial series, we ended up with a csv file called bydate_shortstay_csv.csv. Let's read it in and take a look at it.

# <codecell>

## Read sample data set and convert string dates to datetimes
bydate_df = pd.read_csv('data/bydate_shortstay_csv.csv',parse_dates=['datetime'])

# <codecell>

bydate_df.head()

# <codecell>

bydate_df[1320:1350].values

# <markdowncell>

# With this data frame we can compute all kinds of interesting summary statistics by category, by day of week and time of day. To facilitate this type of "group by" analysis, **pandas** takes what is known as the Split-Apply-Combine approach. The [pandas documentation has a nice discussion](http://pandas.pydata.org/pandas-docs/dev/groupby.html) of this. To really understand split-apply-combine, [check out the article](http://www.jstatsoft.org/v40/i01) by [Hadley Wickham](http://had.co.nz/) who created the **plyr** package for [R](http://www.r-project.org/). I also created a tutorial on [Getting started with Python (with pandas and matplotlib) for group by analysis](http://hselab.org/machinery/content/getting-started-python-pandas-and-matplotlib-group-analysis) that covers some of the basics. A [companion tutorial shows how to do the same analysis using R](http://hselab.org/machinery/content/getting-started-r-plyr-and-ggplot2-group-analysis) instead of Python.

# <markdowncell>

# Pandas provides a `GroupBy` object to facilitate computing aggregate statistics by grouping fields. 

# <codecell>

# Create a GroupBy object for the summary stats    
bydate_dfgrp1 = bydate_df.groupby(['category','binofweek'])

# <codecell>

# Having a group by object makes it easy to compute statistics such as the mean of all of the fields other than the grouping fields.
# You'll see that the result is simply another DataFrame.
bydate_dfgrp1.mean()

# <codecell>

# Let's explore some of the means.
bydate_dfgrp1.mean()[100:120]

# <markdowncell>

# Now that we've seen how the a `GroupBy` object works, let's see how we can compute a whole bunch of summary statistics at once. Specifically we want to compute the mean, standard deviation, min, max and several percentiles. First let's create a slightly different `GroupBy` object.

# <codecell>

bydate_dfgrp2 = bydate_df.groupby(['category','dayofweek','binofday'])

# <markdowncell>

# Now let's define a function that will return a bunch of statistics in a dictionary for a column of data.

# <codecell>

def get_occstats(group, stub=''):
    return {stub+'count': group.count(), stub+'mean': group.mean(), 
            stub+'min': group.min(),
            stub+'max': group.max(), 'stdev': group.std(), 
            stub+'p50': group.quantile(0.5), stub+'p55': group.quantile(0.55),
            stub+'p60': group.quantile(0.6), stub+'p65': group.quantile(0.65),
            stub+'p70': group.quantile(0.7), stub+'p75': group.quantile(0.75),
            stub+'p80': group.quantile(0.8), stub+'p85': group.quantile(0.85),
            stub+'p90': group.quantile(0.9), stub+'p95': group.quantile(0.95),
            stub+'p975': group.quantile(0.975), 
            stub+'p99': group.quantile(0.99)}

# <markdowncell>

# Now we can use the `apply` function to apply the `get_occstats()` function to a data series. We'll create separate output data series for occupancy, arrivals and departures.  

# <codecell>

occ_stats = bydate_dfgrp2['occupancy'].apply(get_occstats)
arr_stats = bydate_dfgrp2['arrivals'].apply(get_occstats)
dep_stats = bydate_dfgrp2['departures'].apply(get_occstats)

# <markdowncell>

# So, what is `occ_stats`?

# <codecell>

type(occ_stats)

# <markdowncell>

# It's a pandas `Series` object. What does its index look like?

# <codecell>

occ_stats.index

# <markdowncell>

# Notice it's a `MultiIndex` with 4 levels: category, dayofweek, binofday, statistic. It would be nice to "un-pivot" the statistic from the index and have it correspond to a set of columns. That's what `unstack()` will do. It will leave us with a `DataFrame` with all of the statistics as columns and a 3 level multi-index of category, dayofweek and binofday. Perfect for plotting.

# <codecell>

occ_stats.unstack()

# <codecell>

occ_stats_summary = occ_stats.unstack()
arr_stats_summary = arr_stats.unstack()
dep_stats_summary = dep_stats.unstack()

print occ_stats_summary[200:220].values # Let's peek into the middle of the table.

# <markdowncell>

# Wouldn't it be nice if Excel Pivot Tables could produce the output above? Why can't they? Because they can't do things like percentiles (or other custom aggregate functions). I love spreadsheets. I teach spreadsheet modeling. However, I find myself using either Python+pandas+matplotlib or R+plyr+ggplot2 more and more frequently for things I used to do in Excel.

# <markdowncell>

# Let's fire these guys out to csv files so we can check them out and maybe play with them in spreadsheet. 

# <codecell>

occ_stats_summary.to_csv('occ_stats_summary.csv')
arr_stats_summary.to_csv('arr_stats_summary.csv')
dep_stats_summary.to_csv('dep_stats_summary.csv')

# <markdowncell>

# The real reason I exported them to csv was to make it easy to read these results back in for Part 3 of this series of tutorials. In Part 3, we'll create some plots using matplotlib based on these summary statistics.

