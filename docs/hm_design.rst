Possible classes
================


Scenario
--------

A *scenario* is the basic unit of analysis and is defined by an input
dataset (Stopdata) and a set of input parameter values.

Is this really an ScenarioInputs object and should we then also have a
ScenarioOutputs object?

Stopdata
--------

This is the primary input data on which Hillmaker is run.

ParameterSet
------------

The input parameters for a scenario.

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

Excel
-----

Pandas has an `ExcelFile` class which uses the xlrd and openpyxd packages.

HDF5
----

PyTables

Including sample stop data with package
=======================================

Much like many R and Python packages that include some test data, be nice to do this with hillmaker.