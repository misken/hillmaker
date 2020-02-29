Things to do to release new version
===================================

Source
------

Update setup.py with new version number

Make sure all changes  on develop branch committed and pushed to GitHub

	$ git checkout master
	$ git merge develop
	$ git push

Tag release on GitHub

	$ git tag -a v0.2.1 -m 'Removed some testing code in bin_of_week but really doing this to get noarch version to conda-forge'
	
	git push origin v0.2.1

PyPi
----

https://python-packaging-user-guide.readthedocs.org/en/latest/

**Source and wheel distribution** ::

  python3 setup.py sdist bdist_wheel

**Upload via twine** ::

hillmaker$ which twine
/home/mark/anaconda3/envs/datasci/bin/twine
(datasci) mark@quercus:~/Documents/development/hillmaker
hillmaker$ twine upload dist/hillmaker-0.2.1*

username is hselab and pw is teddy

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
