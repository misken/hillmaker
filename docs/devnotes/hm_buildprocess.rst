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
    $ git tag -a v0.4.0 -m "Release 0.4.0"
    $ git push origin master
    # Push the tag
    $ git push origin v0.4.0
    $ git checkout develop
    $ git merge --no-ff release-0.4.0
    $ git branch -d release-0.4.0
    

PyPi
----

This is a bit tricky because we are using Anaconda on Linux and
have to make sure we are using the ``python`` and ``pip`` executables
that are in our conda virtual environment (and **NOT** in our
base conda environment)

Using instructions from Real Python tutorial - https://realpython.com/pypi-publish-python-package/#publish-your-package-to-pypi.

Need to install ``build`` and ``twine`` into a conda virtual environment.
Again, make sure you are using the ``pip`` that is part of the 
venv and not the base pip.

.. code::

    $ /PATH/TO/anaconda3/envs/py37/bin/python -m pip install build twine
    $ /PATH/TO/anaconda3/envs/py37/bin/python -m build
    $ twine check dist/*
    # PyPI now using API tokens
    $ twine --repository hillmaker
    $ twine upload dist/*




