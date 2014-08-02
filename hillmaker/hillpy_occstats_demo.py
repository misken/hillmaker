
import pandas as pd

def make_bydatetime(stops_df,infield,outfield,catfield,start_date,end_date,total_str='Total',bin_size_mins=60):
    """
    Create bydatetime table based on user inputs.

    This is the table from which summary statistics can be computed.

    Parameters
    ----------
    D : pandas DataFrame
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

    Returns
    -------
    bydatetime: pandas DataFrame
       The computed bydatetime table as a DataFrame

    Examples
    --------
    >>> bydt_df = make_bydatetime(stops_df,'InTime','OutTime','PatientType',
    ...                        datetime(2014, 3, 1),datetime(2014, 6, 30),'Total',60)


    TODO
    ----

    - add parameter and code to handle occ frac choice
    - generalize to handle choice of arr, dep, occ or some combo of

     Notes
    -----


    References
    ----------


    See Also
    --------
    """

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

