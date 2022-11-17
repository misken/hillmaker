Hillmaker is a Python library

May have some architectural things to learn and ideas to glean from pandas-profiling at
https://github.com/ydataai/pandas-profiling.



Possible features
=================

Config files
----------------
https://stackoverflow.com/questions/65283208/toml-vs-yaml-vs-strictyaml



Possible classes
================


Scenario
--------

An *scenario* is the basic unit of analysis and is defined by an input
dataset (stop data) and a set of input parameter values.

Properties
^^^^^^^^^^

name : string
    Scenario identifier

stop_data : pandas DataFrame

in_field : string
   Name of column in D to use as arrival datetime

out_field : string
   Name of column in D to use as departure datetime

cat_field : string
   Name of column in D to use as category field

start_date : datetime
   Start date for the analysis

end_date : datetime
   End date for the analysis

total_str : string
   Value to use for the totals

bin_size_mins : int
   Bin size in minutes. Should divide evenly into 1440.



stop_data
------------

This is the primary input data on which Hillmaker is run.

ParameterSet
------------

The input parameters for a scenario.

Hillmaker
---------

The calculation engine

Hills
-----

Output data



Stopdata reading and connections and conversion to DataFrame
============================================================

See Chapter 6 of the pandas book.


CSV
---

Easy to read in a csv file to a DataFrame.
- user would need to export database table to csv
- could give user options exposed by read_csv method such as ability to skip comments, general separator choice, etc.

Pickles
-------

Easy to read in a pickle file containing a pandas DataFrame
- how does this work across Python versions (both major and minor)?
- perhaps too Python specific and remember reading some "bad" things about pickle format

Excel
-----

Pandas has an `ExcelFile` class which uses the xlrd and openpyxd packages.

HDF5
----

PyTables

Including sample stop data with package
=======================================

Much like many R and Python packages that include some test data, be nice to do this with hillmaker.

User interface
==============

What to do?

https://github.com/chriskiehl/Gooey

https://github.com/pinterest/thrift-tools

https://testdriven.io/blog/build-spa-with-python-part-1/

Model projects
==============

https://github.com/rasbt/biopandas

https://github.com/bloomberg/bqplot

https://github.com/pinterest/thrift-tools

https://github.com/quantopian/pyfolio


