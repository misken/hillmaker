# hillmaker

**hillmaker** is a Python package that computes time of day and day of week specific
occupancy statistics from transaction data containing arrival and departure
timestamps. Typical use is for capacity planning problems in places like
hospital emergency departments, surgical recovery rooms or any system in which
entities arrive, occupy capacity for some amount of time, and then depart. It
gets its name from the hill-like nature of plots based on temporal occupancy
statistics.

![hillmaker Screenshot](docs/images/ssu_occ_1.png "hillmaker screenshot")

- Takes a pandas DataFrame or csv file as the input data type
- Functions for computing arrival, departure and occupancy summary statistics
  by time of day, day of week, and entity category based on a pandas DataFrame containing one
  record per visit.
- Functions for computing arrival, departure and occupancy for each datetime
  bin in the analysis period, by zero or one category fields.
- Select any time bin size (minutes) that divides evenly into a day.
- Output statistics includes sample size, mean, min, max, standard deviation,
  coefficient of variation, standard error, skew, kurtosis, and percentiles.
- Weekly and day of week plots can be created.
- Outputs are stored in a dictionary containing pandas dataframes and as matplotlib figures. These can be accessed by methods for further post-processing or for exporting to external files.
- Requires Python >= 3.10, pandas >= 1.5.0, numpy >= 1.22
- MIT License

Where to get it
---------------

* Source code: http://github.com/misken/hillmaker
* Binary and source on PyPI: https://pypi.python.org/pypi/hillmaker
* Documentation: Coming soon

Future plans
------------

A new release will happen in November of 2023. There are major changes to the API including a new object oriented way of working with hillmaker and expansion of its plotting capabilities. There is also actual documentation that will be hosted at Read the Docs. 

Quick Start
-----------

A companion repo, https://github.com/misken/hillmaker-examples/ contains
Jupyter notebooks and Python scripts illustrating the use of hillmaker. You can
also find example notebooks within this main hillmaker repo. You can see the most recent one at https://github.com/misken/hillmaker-examples/blob/main/notebooks/basic_usage_shortstay_unit_046.ipynb.

The source and a binary wheel are available from PyPi. You can install using pip. 

    pip install tomli  # Not necessary if using Python >= 3.11
    pip install hillmaker


Learn more about hillmaker
--------------------------
Hillmaker has been around in various forms for over 30 years. A few
blog posts describing how it works are available though many things
about the API as well as the computational guts of hillmaker have
changed with this recent version.

* [Computing occupancy statistics with Python - 1 of 3](https://bitsofanalytics.org/posts/hillmaker-bydate-demo/hillpy_bydate_demo.html)
* [Computing occupancy statistics with Python - 2 of 3](https://bitsofanalytics.org/posts/hillmaker-occstats-demo/hillpy_occstats_demo.html)
* [Plotting occupancy statistics with Python - 3 of 3](https://bitsofanalytics.org/posts/hillmaker-plotting-recipe/hillpy_plotting_recipe.html)
* [Analyzing bike share usage](https://bitsofanalytics.org/posts/basic-usage-cycleshare/basic_usage_cycleshare.html)
* [Using hillmaker from R with reticulate](https://bitsofanalytics.org/posts/hillmaker-r-sfcs/hillmaker_r_sfcs.html)
* [Numpy speeds up hillmaker dramatically](https://bitsofanalytics.org/posts/hillmaker-speedup/)

I published [a paper a long time ago regarding the use of hillmaker in practice](https://www.researchgate.net/publication/220385298_Modeling_and_Analysis_of_Occupancy_Data_A_Healthcare_Capacity_Planning_Application).
It describes an ancient version of hillmaker but does describe typical use cases.
