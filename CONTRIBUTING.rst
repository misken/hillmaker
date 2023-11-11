Contributing
============

There are many ways of contributing to the package, all of which are greatly
appreciated. See below for examples of how you can make a contribution.


Bug reports
-----------

Report bugs at https://github.com/misken/hillmaker/issues.

If you are reporting a bug, please include

* Version number of hillmaker
* Steps to reproduce bug
* Expected behavior
* Actual behavior
* Any details about your local setup that might be helpful in troubleshooting,
  such as operating system, python version, conda/pip environment etc.


Propose features or improvements
--------------------------------

Feature proposals can be submitted at https://github.com/misken/hillmaker/issues.
If you are using hillmaker for a project in the healthcare industry, please include the context and motivation
for the feature request.


Contribute code
---------------

If you have the capacity to fix bugs yourself, or implement new features, this
is of course very welcome. In this case, the preferred approach is as follows:

1.  Open an issue on https://github.com/misken/hillmaker/issues, where you
    describe the bug/feature and your proposed implementation idea at a high level.

2.  Get feedback from the development team and agree on the way forward.

3.  Fork the hillmaker repo on GitHub and clone your fork locally::

     $ cd name_of_dev_dir
     $ git clone git@github.com:your_name_here/hillmaker.git .

4.  Use ``conda`` or ``virtualenv`` to create an isolated development
    environment. For instance, assuming that ``conda`` is installed, use::

     $ cd name_of_dev_dir
     $ conda env create -f environment.yml
     $ conda activate hillmaker
     $ pip install -e .[dev]

5.  Use ``pytest`` to create one or more (failing) tests that demonstrate the
    bug/feature. Make local changes to the code until the test passes. Running
    tests is simple::

     $ cd name_of_dev_dir
     $ pytest

6.  Bump the minor version number (in ``__init__.py``) and make a descriptive
    entry in ``CHANGELOG.md``. Make changes to the documentation if necessary.
    New features should be documented by creating a new example, or editing
    an old one.

7.  Commit your changes and push your branch to GitHub::

     $ git add .
     $ git commit -m "Your detailed description of your changes."
     $ git push origin name-of-your-bugfix-or-feature

8.  Submit a pull request through the GitHub website. The developers may
    suggest changes to the code before the request is ultimately accepted.