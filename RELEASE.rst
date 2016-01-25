
=============
Release Notes
=============

This is the list of changes to hillmaker between each release. For full details,
see the commit logs at http://github.com/misken/hillmaker

What is it
----------

**hillmaker** is a Python package that computes time of day and day of week specific
occupancy statistics from transaction data containing arrival and departure
timestamps. Typical use is for capacity planning problems in places like
hospital emergency departments, surgical recovery rooms or any system in which
entities arrive, occupy capacity for some amount of time, and then depart. It
gets its name from the hill-like nature of plots based on temporal occupancy
statistics.

Where to get it
---------------

* Source code: http://github.com/misken/hillmaker
* Binary and source on PyPI: https://pypi.python.org/pypi/hillmaker
* Binary on Anaconda.org: http://anaconda.org/hselab/hillmaker
* Documentation: Coming soon


hillmaker 0.1.1
===============

**Release date:** 2016-01-24

**New features**

**Improvements to existing features**

**API Changes**

**Bug Fixes**

  * Removed duplicate output of category, bin of day and day of week fields (GH0018_)

.. _GH0018: https://github.com/misken/hillmaker/issues/18




hillmaker 0.1.0
===============

**Release date:** 2016-01-22

**New features**

:mod:`hillmaker` consists of the following things and features

 * Takes a pandas DataFrame as the input data type
 * Functions for computing arrival, departure and occupancy summary statistics
   by time bin of day and day of week based on a pandas DataFrame containing one
   record per visit.
 * Functions for computing arrival, departure and occupancy for each datetime
   bin in the analysis period.
 * Select any time bin size (minutes) that divides evenly into a day.
 * Optionally specify one or more categories to ignore in the analysis.
 * Output statistics includes sample size, mean, min, max, standard deviation,
   coefficient of variation, standard error, skew, kurtosis, and a whole slew
   of percentiles (50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 97.5, 99).
 * Output CSV files are written by default but can be supressed.
 * Optionally capture outputs as a dictionary of pandas DataFrames for further
   post-processing (e.g. plot creation).
