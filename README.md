# hillmaker

**hillmaker** is a Python package that computes time of day and day of week specific
occupancy statistics from transaction data containing arrival and departure
timestamps. Typical use is for capacity planning problems in places like
hospital emergency departments, surgical recovery rooms or any system in which
entities arrive, occupy capacity for some amount of time, and then depart. It
gets its name from the hill-like nature of plots based on temporal occupancy
statistics.

![hillmaker Screenshot](/docs/hillmaker-user-guide/images/ssu_occ_1.png "hillmaker screenshot")

- Takes a pandas DataFrame as the input data type
- Functions for computing arrival, departure and occupancy summary statistics
  by time bin of day and day of week based on a pandas DataFrame containing one
  record per visit.
- Functions for computing arrival, departure and occupancy for each datetime
  bin in the analysis period.
- Select any time bin size (minutes) that divides evenly into a day.
- Optionally specify one or more categories to ignore in the analysis.
- Output statistics includes sample size, mean, min, max, standard deviation,
  coefficient of variation, standard error, skew, kurtosis, and a whole slew
  of percentiles (50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 97.5, 99).
- Output CSV files are written by default but can be supressed.
- Optionally capture outputs as a dictionary of pandas DataFrames for further
  post-processing (e.g. plot creation).
- Requires Python 3 and pandas
- Apache 2.0 licensed

  # Quick Start

  A companion repo, https://github.com/misken/hillmaker-examples/ contains
  IPython notebooks and Python scripts illustrating the use of hillmaker.

  In particular, the following IPython notebook explains how to get and
  use hillmaker.

  https://github.com/misken/hillmaker-examples/blob/master/notebooks/basic_win_usage_shortstay_unit.ipynb

  The notebook above is aimed at Windows users of the MS Access version of hillmaker. It talks them through
  installing hillmaker using Conda. Both Win-64 and Linux-64 versions are available.

      conda install -c https://conda.anaconda.org/hselab hillmaker

  The source and a binary wheel are available from PyPi. You can install using pip:

      pip install hillmaker


  More examples and documentation are on the way.
