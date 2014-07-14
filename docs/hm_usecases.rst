Hillmaker Use Cases
===================

Create historical tabular occupancy summaries using GUI front end
-----------------------------------------------------------------

This is the prototypical use case. We have a tabular set of data with
in-out timestamp fields and one or more dimension fields by which we
want to summarize occupancy (in addition to time dimension of DOW and
TOD). 

* The user would like to enter scenario inputs via a user friendly form
* The input stop data is in either a delimited text file, xlsx file, a SQL 
database table or view (SQL Server, MySQL, or sqlite), an MS Access table
* Our desired output is the "by datetime" table as well as the
weekly summaries in delimited text form

Run multiple scenarios using Python program or IPython notebook
----------------------------------------------------------------

User would like to easily feed a set of "scenario" specifications to a Python
function that produces the tabular outputs described above.

Limit output to just the "by datetime" table
--------------------------------------------

Whether via GUI or code, want to be able to specify which output tables
we want.

Input specification
--------------------

General bin size choice
Percentile method choice
Bin contribution choices
Analysis date range should have some appropriateness check
Stop data should be checked for gaps or potential errors
