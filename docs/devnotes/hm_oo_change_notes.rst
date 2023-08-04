Scenario class
=================

Added a Scenario class that contains

- make_hills() method
- get_plot(self, flow_metric='occupancy', day_of_week='week') method


General
========

In process of adding type hints

Bug fixes
=========

Edge bins not implementing full bins option - see https://github.com/misken/hillmaker/issues/43. This underscores need for more testing.

Planned features
================

- Allow user to specify series to include on plots
- LOS summary
- create Scenario methods for doing the various stages of make_hills and then modify make_hills to call them
