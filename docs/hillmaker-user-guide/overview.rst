.. _overview:

.. currentmodule:: hillmaker


******************
What is hillmaker?
******************

Hillmaker is a Python package that facilitates statistical occupancy analysis of
systems involving the arrival and departure of discrete entities. It is
particularly useful when time of day and day of week effects are of interest. It
gets its name from the hill-like nature of occupancy statistics plotted by time
of day and day of week (see plot below). The original version of Hillmaker was
developed many years ago (using MS Access and VBA) in response to capacity
planning problems arising in health care delivery systems such as hospitals and
outpatient clinics. Typical examples include emergency departments,
post-anesthesia care units, inpatient nursing units, and clinics. However,
hillmaker can be used in any domain in which entities "arrive", occupy capacity
for some amount of time, and then "depart". For example, work in process within
a manufacturing system can be analyzed using the entry and exit times of each
part flowing into some process or stage of interest. The only data requirement
is the arrival and departure times for each entity. Optionally, each entity
can be labelled or classified as belonging to some category or class. If done,
in addition to overall, occupancy statistics by category are also computed.

----------------------------------
Example - Hospital short stay unit
----------------------------------

Hospital short stay units (SSU) provide a place to care for patients that don't
need to admitted but might stay for up to a day. Patients often use a SSU to
undergo or recover from a therapy or procedure. Consider a simplified SSU caring
for fived different patient types: ART (arterialgram), CAT (post cardiac-cath),
MYE (myelogram), IVT (IV therapy), and OTH (other).

Here's a snippet of a data file (CSV) containing records of patients visiting
the SSU (the entire file contains just under 60,000 records corresponding
to three months of SSU activity):

  PatID,InRoomTS,OutRoomTS,PatType
  1,1/1/1996 7:44,1/1/1996 8:50,IVT
  2,1/1/1996 8:28,1/1/1996 9:20,IVT
  3,1/1/1996 11:44,1/1/1996 13:30,MYE
  4,1/1/1996 11:51,1/1/1996 12:55,CAT
  5,1/1/1996 12:10,1/1/1996 13:00,IVT
  6,1/1/1996 14:16,1/1/1996 15:35,IVT
  7,1/1/1996 14:40,1/1/1996 15:25,IVT
  8,1/1/1996 17:25,1/1/1996 19:00,CAT
  9,1/2/1996 6:17,1/2/1996 8:25,MYE
  10,1/2/1996 6:35,1/2/1996 8:30,ART

The `InRoomTS` and `OutRoomTS` fields contain timestamps corresponding to when
the patient entered and exited the SSU. `PatType` is the category for each
patient. In order to help develop SSU staffing plans, we would like to compute
the average and 95'th percentile of SSU occupancy by day of week and hour of
day. In addition to overall occupancy statistics, we'd like to compute the same
statistics by patient type. And, it's not just occupancy we are interested in.
We also want to compute these statistics for arrivals and departures from the
SSU. From such summaries we can create plots to visualize the results.

.. image:: images/ssu_occ_1.png



The key inputs needed for running hillmaker are the name of the `pandas
<http://pandas.pydata.org/>`_ Dataframe containing the transaction records, the
datetime field corresponding to the entry time, the datetime field corresponding
to the exit time, the (optional) field corresponding to the categories, the date
range for selecting transaction records for the analysis (the *analysis
period*), and the *time bin* size (in minutes). While hillmaker has a number of
options, the  simplest use case involves importing hillmaker and pandas, reading
the data file into a Dataframe and making a single function call. The default
timebin size is one hour.

::

  import pandas as pd
  import hillmaker as hm

  # Read data from CSV file into a pandas dataframe
  stops_fn = '../data/ShortStay.csv'
  stops_df = pd.read_csv(stops_fn, parse_dates=['InRoomTS','OutRoomTS'])

  # Required inputs
  scenario = 'ss_example_1'
  in_fld_name = 'InRoomTS'
  out_fld_name = 'OutRoomTS'
  cat_fld_name = 'PatType'
  start = '1/1/1996'
  end = '3/30/1996 23:45'

  # Run hillmaker
  hm.make_hills(scenario, stops_df, in_fld_name, out_fld_name,
                start, end, cat_fld_name)


hillmaker outputs a number of DataFrames containing the results of the
analysis. One of these DataFrames contains the summary statistics used to
drive the plot shown above. Here's a little bit of what that Dataframe looks
like after being exported to a CSV file.

.. image:: images/example_1_occ.png


More details on hillmaker output are described in SECTION OUTPUT.



****************
Package overview
****************

:mod:`hillmaker` consists of the following things and features

 * Functions for computing arrival, departure and occupancy summary statistics
   by time bin of day and day of week based on a pandas Dataframe containing one
   record per visit.
 * Functions for computing arrival, departure and occupancy for each datetime
   bin in the analysis period.
 * Select any time bin size (minutes) that divides evenly into a day.
 * Optionally specify one or more categories to ignore in the analysis.
 * Output statistics includes sample size, mean, min, max, standard deviation,
   coefficient of variation, standard error, skew, kurtosis, and a whole slew
   of percentiles (50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 97.5, 99).
 * Output CSV files are written by default but can be supressed.
 * Optionally capture outputs as a dictionary of pandas Dataframes for further
   post-processing (e.g. plot creation).




Why more than 1 data structure?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The best way to think about the pandas data structures is as flexible
containers for lower dimensional data. For example, DataFrame is a container
for Series, and Panel is a container for DataFrame objects. We would like to be
able to insert and remove objects from these containers in a dictionary-like
fashion.

Also, we would like sensible default behaviors for the common API functions
which take into account the typical orientation of time series and
cross-sectional data sets. When using ndarrays to store 2- and 3-dimensional
data, a burden is placed on the user to consider the orientation of the data
set when writing functions; axes are considered more or less equivalent (except
when C- or Fortran-contiguousness matters for performance). In pandas, the axes
are intended to lend more semantic meaning to the data; i.e., for a particular
data set there is likely to be a "right" way to orient the data. The goal,
then, is to reduce the amount of mental effort required to code up data
transformations in downstream functions.

For example, with tabular data (DataFrame) it is more semantically helpful to
think of the **index** (the rows) and the **columns** rather than axis 0 and
axis 1. And iterating through the columns of the DataFrame thus results in more
readable code:

::

    for col in df.columns:
        series = df[col]
        # do something with series

Mutability and copying of data
------------------------------

All pandas data structures are value-mutable (the values they contain can be
altered) but not always size-mutable. The length of a Series cannot be
changed, but, for example, columns can be inserted into a DataFrame. However,
the vast majority of methods produce new objects and leave the input data
untouched. In general, though, we like to **favor immutability** where
sensible.

Getting Support
---------------

The first stop for pandas issues and ideas is the `Github Issue Tracker
<https://github.com/pydata/pandas/issues>`__. If you have a general question,
pandas community experts can answer through `Stack Overflow
<http://stackoverflow.com/questions/tagged/pandas>`__.

Longer discussions occur on the `developer mailing list
<http://groups.google.com/group/pystatsmodels>`__, and commercial support
inquiries for Lambda Foundry should be sent to: support@lambdafoundry.com

Credits
-------

pandas development began at `AQR Capital Management <http://www.aqr.com>`__ in
April 2008. It was open-sourced at the end of 2009. AQR continued to provide
resources for development through the end of 2011, and continues to contribute
bug reports today.

Since January 2012, `Lambda Foundry <http://www.lambdafoundry.com>`__, has
been providing development resources, as well as commercial support,
training, and consulting for pandas.

pandas is only made possible by a group of people around the world like you
who have contributed new code, bug reports, fixes, comments and ideas. A
complete list can be found `on Github <http://www.github.com/pydata/pandas/contributors>`__.

Development Team
----------------

pandas is a part of the PyData project. The PyData Development Team is a
collection of developers focused on the improvement of Python's data
libraries. The core team that coordinates development can be found on `Github
<http://github.com/pydata>`__. If you're interested in contributing, please
visit the `project website <http://pandas.pydata.org>`__.

License
-------

.. literalinclude:: ../../LICENSE
