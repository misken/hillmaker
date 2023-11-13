# Changelog

This is the list of notable changes to hillmaker between each release.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] - 2023-11-??

### Added

- an objected oriented API ([#37][d37])
- added many input parameters for controlling hillmaker computations and outputs ([#50][i50] [#51][i51], [#54][i54])
- can specify inputs via TOML formatted config file if desired ([#33][i33])
- length of stay summary report ([#26][i26])
- input validation handled via a `pydantic <https://docs.pydantic.dev/latest/>`_ model, ([#34][i34])
- documentation at https://hillmaker.readthedocs.io/en/latest/intro.html ([#9][i9])
- unit tests for occupancy computations ([#14][i14])
- added extensive conservation of flow checks ([#25][i25])
- detailed logging ([#21][i21])


### Changed

- CLI input arguments for controlling hillmaker computations and outputs ([#55][i55])
- function based API input arguments for controlling hillmaker computations and outputs ([#55][i55])
- enhanced plotting capabilities ([#36][i36])
- added examples to docstrings for API related elements ([#56][i56])


### Fixed

- edge_bins = 2 (entire bin) was being treated as edge_bins = 1 (fractional arrival and departure bins) ([#43][i43])

## [0.4.6] - 2023-07-25

### Fixed

- if no category field is specified, the plots were not being generated. ([#42][i42])

## [0.4.5] - 2022-11-20

### Examples

**New features and API changes**

- moved examples folder to project root
- updated dependencies to python>=3.9, pandas>=1.4, numpy>=1.22
- updated paths in ad-hoc tests to reflect new folder layout

hillmaker 0.4.4
===============

**Release date:** 2022-07-22

**New features and API changes**

- adding weekly and dow plots of arrivals, departures, occupancy

hillmaker 0.4.3
===============

**Release date:** 2022-07-19

**New features and API changes**

- can use TOML formatted config file for command line args
- added percentiles to CLI
- renamed verbose argument to verbosity



hillmaker 0.4.2
===============

**Release date:** 2022-07-15

**New features**

- Added option to treat missing departure timestamps as censored data.

**Bug Fixes**

- disallowed missing entry timestamps

hillmaker 0.4.1
===============

**Release date:** 2022-07-14


**Bug Fixes**

- date range sanity check had copy paste error with start and end variables
- removed old licensing references
- fixed typos in basic usage notebook
- added hillmaker related blog post links to readme

hillmaker 0.4.0
===============

**Release date:** 2022-07-14

**New features**

- added basic usage explainer notebook

**Bug Fixes**

- adjusted arrivals and departures by bin arrays to account for stops with arrivals or departures outside the analysis range


hillmaker 0.3.0
===============

**Release date:** 2022-05-13

**New features**

- the main new feature is speed
- added CLI
- added flow conservation checks
- added logging

**Improvements to existing features**

- Greatly improved speed by moving many computations into numpy arrays and vectorizing things.

**API Changes**

- deprecated use of multiple category fields and reverted to previous functionallity of a single (optional)
category field. Multiple categories are best handled with composite keys.

**Bug Fixes**

hillmaker 0.2.3
===============

**Release date:** 2020-03-18

**Bug Fixes**

- replaced call to deprecated time.clock() with time.process_time()

hillmaker 0.2.0
===============

**Release date:** 2020-02-04

**New features**

* Added `edge_bins` parameter to control how occupancy contribution is computed
for arrival and departure bins. 1=fractional contribution (default), 2=whole bin

* Multiple category fields allowed.(GH0017_)

.. _GH0017: https://github.com/misken/hillmaker/issues/17

    totals: int, default 1
        0=no totals, 1=totals by datetime, 2=totals bydatetime as well as totals for each field in the
        catfields (only relevant for > 1 category field)
        
* Can specify a field to use as occupancy weights. This can be useful
for building plots of workload instead of occupancy.

**Improvements to existing features**

**API Changes**

**Bug Fixes**

* Replace deprecated sortlevel() by sort_index() (GH0020_)

.. _GH0017: https://github.com/misken/hillmaker/issues/20



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

[d37]: https://github.com/misken/hillmaker/discussions/37
[i9]: https://github.com/misken/hillmaker/issues/9
[i14]: https://github.com/misken/hillmaker/issues/14
[i21]: https://github.com/misken/hillmaker/issues/21
[i25]: https://github.com/misken/hillmaker/issues/25
[i26]: https://github.com/misken/hillmaker/issues/26
[i33]: https://github.com/misken/hillmaker/issues/33
[i34]: https://github.com/misken/hillmaker/issues/34
[i36]: https://github.com/misken/hillmaker/issues/36
[i42]: https://github.com/misken/hillmaker/issues/42
[i43]: https://github.com/misken/hillmaker/issues/43
[i50]: https://github.com/misken/hillmaker/issues/50
[i51]: https://github.com/misken/hillmaker/issues/51
[i54]: https://github.com/misken/hillmaker/issues/54
[i55]: https://github.com/misken/hillmaker/issues/55
[i56]: https://github.com/misken/hillmaker/issues/56
