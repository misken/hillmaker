Scenario class
=================

Added a Scenario class that contains

- make_hills() method
- get_plot(self, flow_metric='occupancy', day_of_week='week') method

https://datascience.statnett.no/2020/05/11/how-we-validate-data-using-pydantic/

Mired in a mess of trying to figure out the API for Scenario and related pydantic model and legacy functions like make_datetime and make_hills. Be nice to still have these usable but how best to do parameter validation in that case.


General
========

- added type hints

Bug fixes
=========

* Edge bins not implementing full bins option - see https://github.com/misken/hillmaker/issues/43. This underscores need for more testing.

Planned features
================

- create Scenario methods for doing the various stages of make_hills and then modify make_hills to call them
- Allow user to specify series to include on plots
- LOS summary

