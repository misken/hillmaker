Things to do create new feature and release new version
=======================================================

Using the gitflow model as outlined in `A successful git branching model <https://nvie.com/posts/a-successful-git-branching-model/>`_.

Creating a new feature
-----------------------

Create a new branch off of ``develop`` branch.

**Make sure all commits on ``develop`` are done.

.. code::

    git checkout -b mynewfeature develop
    
Do the coding to add new feature.

Merge feature branch back into develop
---------------------------------------

When feature is ready for merging:

.. code::

   $ git checkout develop
   $ git merge --no-ff mynewfeature 
   # Delete feature branch if you are sure merge was successful
   $ git branch -d mynewfeature
   # git push origin develop
   
Now the ``develop`` branch includes the new features and we have 
deleted the feature branch.

Continue minor work on develop branch
--------------------------------------

Now there may be some tidying to do on the ``develop`` branch before
we are ready to do a new release. Make sure all commits are done before
moving on to release branch.

Creating a new release branch
-----------------------------

Do this when just about ready to release new version. 

.. code::

    # Create release branch off of develop
    $ git checkout -b release-0.4.0 develop

Now do last minute fixes and updates such as:

* bump the version number in setup.py
* add to the release notes doc
* make any necessary readme.md changes
* fix any last second bugs

When ready to release, commit all changes

.. code::

    $ git commit -a -m "Bumped version number to 0.4.0, updated readme and release notes"
    
Now we will do the following:

* merge the release branch into the master branch
* tag (annotated) the master branch with release number
* merge the release branch back into the develop branch so that develop has all the last minute changes we just did
* delete the release branch

.. code::

    $ git checkout master
    $ git merge --no-ff release-0.4.0
    $ git tag -a 0.4.0 -m "Release 0.4.0"
    $ git push origin master
    # Push the tag
    $ git push origin 0.4.0
    $ git checkout develop
    $ git merge --no-ff release-0.4.0
    $ git branch -d release-0.4.0
    



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

  python setup.py sdist bdist_wheel

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
