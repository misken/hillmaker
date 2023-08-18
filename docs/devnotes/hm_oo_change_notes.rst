Scenario class
=================

Added a Scenario class that contains

- make_hills() method
- get_plot(self, flow_metric='occupancy', day_of_week='week') method
- get_summary_df and get_bydatetime_df were added as methods
- the class methods are just wrappers that call the module level functions. This allows us to not break the existing API and allow hillmaker to be used in an OO or non-OO way.



- the Scenario class holds all of the input parameters as well as a `hills` attribute that is populated by `hillmaker.make_hills()`.
- the Scenario.make_hills()` method is a wrapper for the module level `make_hills()` function. By doing this, the legacy interface to `make_hills()` is maintained (a set of kwargs).
- if `hillmaker.make_hills()` is called directly, a `Scenario` instance is created so that validation and transformation can be done automatically.

See hillmaker_oo_050.ipynb notebook for more details and examples of use.

General
========

- added type hints

Bug fixes
=========

* Edge bins not implementing full bins option - see https://github.com/misken/hillmaker/issues/43. This underscores need for more testing.

Planned features
================

- formal tests
- documentation
- create Scenario methods for doing the various stages of make_hills and then modify make_hills to call them
- Allow user to specify series to include on plots
- LOS summary

Resources
============

- https://datascience.statnett.no/2020/05/11/how-we-validate-data-using-pydantic/

