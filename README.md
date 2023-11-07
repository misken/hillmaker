# hillmaker

**hillmaker** is a Python package that computes time of day and day of week specific
occupancy statistics from transaction data containing arrival and departure
timestamps. Typical use is for capacity planning problems in places like
hospital emergency departments, surgical recovery rooms or any system in which
entities arrive, occupy capacity for some amount of time, and then depart. It
gets its name from the hill-like nature of plots based on temporal occupancy
statistics.

![hillmaker Screenshot](docs/images/example1_occupancy_week.png "hillmaker screenshot")

- usable via a CLI, a function based API and and objected oriented API
- takes a pandas DataFrame or csv file as the input data type
- computes arrival, departure and occupancy summary statistics
  by time of day, day of week, and entity category based on a dataframe containing one
  record per visit.
- computes arrival, departure and occupancy for each datetime bin in a specified date range
- select any time bin size (minutes) that divides evenly into a day.
- output statistics includes sample size, mean, min, max, standard deviation,
  coefficient of variation, standard error, skew, kurtosis, and percentiles.
- weekly and day of week plots can be created by default or on demand; numerous plot related input parameters are available,
- summary report for length of stay automatically created
- outputs are stored in a dictionary containing pandas dataframes and as matplotlib figures. These can be accessed by methods for further post-processing or for exporting to external files.
- Requires Python >= 3.10, pandas >= 1.5.0, numpy >= 1.22, pydantic >= 2.1.1, seaborn >= 0.12.2, matplotlib >= 3.7.1, tomli >= 2.0.1 if not using Python 3.11
- MIT License

See `Release Notes <https://github.com/misken/hillmaker/blob/develop/RELEASE.rst>`_ for details on latest and older versions.

Where to get it
---------------

* Source code: http://github.com/misken/hillmaker
* Binary and source on PyPI: https://pypi.python.org/pypi/hillmaker
* Documentation: https://hillmaker.readthedocs.io/en/latest/intro.html
* More Examples: See notebooks and scripts at http://github.com/misken/hillmaker-examples

Quick Start
-----------

See the [Getting Started](https://hillmaker.readthedocs.io/en/latest/getting_started.html) page in the hillmaker docs.
Also, companion repo, https://github.com/misken/hillmaker-examples/ contains
Jupyter notebooks and Python scripts illustrating the use of hillmaker. 

Installation
-------------

You can install using pip. 

    pip install tomli  # Not necessary if using Python >= 3.11
    pip install hillmaker


Learn more about hillmaker
--------------------------

See the [History](https://hillmaker.readthedocs.io/en/latest/history.html) page at the hillmaker docs.
