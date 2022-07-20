# hillmaker

**hillmaker** is a Python package that computes time of day and day of week specific
occupancy statistics from transaction data containing arrival and departure
timestamps. Typical use is for capacity planning problems in places like
hospital emergency departments, surgical recovery rooms or any system in which
entities arrive, occupy capacity for some amount of time, and then depart. It
gets its name from the hill-like nature of plots based on temporal occupancy
statistics.

![hillmaker Screenshot](/docs/hillmaker-user-guide/images/ssu_occ_1.png "hillmaker screenshot")

- Takes a pandas DataFrame or csv file as the input data type
- Functions for computing arrival, departure and occupancy summary statistics
  by time of day, day of week, and entity category based on a pandas DataFrame containing one
  record per visit.
- Functions for computing arrival, departure and occupancy for each datetime
  bin in the analysis period, by zero or one category fields.
- Select any time bin size (minutes) that divides evenly into a day.
- Output statistics includes sample size, mean, min, max, standard deviation,
  coefficient of variation, standard error, skew, kurtosis, and percentiles.
- Output CSV files are written by default but can be supressed.
- Optionally capture outputs as a dictionary of pandas DataFrames for further
  post-processing (e.g. plot creation).
- Requires Python 3.7+ and pandas 1.2.0+
- MIT License

Where to get it
---------------

* Source code: http://github.com/misken/hillmaker
* Binary and source on PyPI: https://pypi.python.org/pypi/hillmaker
* Documentation: Coming soon

Quick Start
-----------

A companion repo, https://github.com/misken/hillmaker-examples/ contains
Jupyter notebooks and Python scripts illustrating the use of hillmaker.

You can see an html versions of basic usage notebooks at:

- [basic usage notebook for v0.4.3](https://misken.github.io/hillmaker-examples/basic_usage_shortstay_unit_043.html)
- [basic usage notebook for v0.4.0-2](https://misken.github.io/hillmaker-examples/basic_usage_shortstay_unit_040.html).


The source and a binary wheel are available from PyPi. You can install using pip: 

    pip install hillmaker


Learn more about hillmaker
--------------------------
Hillmaker has been around in various forms for over 30 years. A few
blog posts describing how it works are available though many things
about the API as well as the computational guts of hillmaker have
changed with this recent version.

* [Computing occupancy statistics with Python - 1 of 3](https://misken.github.io/blog/hillpy_bydate_demo/)
* [Computing occupancy statistics with Python - 1 of 3](https://misken.github.io/blog/hillpy_occstats_demo/)
* [Plotting occupancy statistics with Python - 3 of 3](https://misken.github.io/blog/hillpy_plotting_matplotlib_basic_recipe/)
* [Analyzing bike share usage](https://misken.github.io/blog/basic_usage_cycleshare/)
* [Using hillmaker from R with reticulate](https://misken.github.io/blog/hillmaker_r_sfcs/)
* [Numpy speeds up hillmaker dramatically](https://misken.github.io/blog/hillmaker_030_released/)

I published [a paper a long time ago regarding the use of hillmaker in practice](https://www.researchgate.net/publication/7322712_Hillmaker_An_open_source_occupancy_analysis_tool).
