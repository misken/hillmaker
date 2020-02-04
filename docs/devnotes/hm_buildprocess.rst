Things to do to release new version
===================================

Source
------

Update setup.py with new version number

Make sure all changes committed and pushed to GitHub

Tag release on GitHub

PyPi
----

https://python-packaging-user-guide.readthedocs.org/en/latest/

**Source distribution** ::

  python setup.py sdist
  python setup.py sdist --formats=zip

**Wheel distribution** ::

  python setup.py bdist_wheel

**Upload via twine** ::

  twine upload dist/hillmaker-x.x.x* -p password

Anaconda.org
------------

Increment version number in recipes/hillmaker/meta.yaml

  package:
    name: hillmaker
    version: "0.1.1"

  source:
    git_rev: v0.1.1
    git_url: https://github.com/misken/hillmaker

::

  cd ~/Documents/development/recipes
  conda build hillmaker

Now need to upload to Anaconda.org ::

  # Get to appropriate dir
  cd ~/anaconda3/conda-bld/noarch
  # Login to anaconda if not already logged in
  anaconda login
  # Upload the file
  anaconda upload <bz2 filename>
