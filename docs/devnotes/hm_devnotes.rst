Best practices for Python development
--------------------------------------

https://gist.github.com/sloria/7001839

https://third-bit.com/sdxpy/intro/

Simon Willonson's posts on CLI design and dev in general
--------------------------------------------------------

https://simonwillison.net/2023/Sep/30/cli-tools-python/
https://simonwillison.net/2022/Oct/29/the-perfect-commit/
https://simonwillison.net/2022/Nov/26/productivity/
https://simonwillison.net/2021/Aug/28/dynamic-github-repository-templates/
https://simonwillison.net/2020/Feb/11/cheating-at-unit-tests-pytest-black/

Originally the 'develop' branch was going to be for the OO design version. However, after thinking about it
and talking with JW, I think this branch will now focus on creating a solid guts version, non OO, that can
be used from a python script or interactively. It will just focus on the base computations, a text in and text out IO
model, and illustration of various use cases via IPython notebooks. This will set the foundation for the OO
version that will come next.

Development environment
-----------------------

Created a conda environment called `datascicore`. It does NOT
contain the hillmaker package. 



Git workflows
-------------

http://blog.endpoint.com/2014/05/git-workflows-that-work.html

How to create a well behaved Python command line application
------------------------------------------------------------

[http://www.curiousvenn.com/2012/08/pycon-australia-2012-tutorial-1-notes/]( http://www.curiousvenn.com/2012/08/pycon-australia-2012-tutorial-1-notes/)
Handle input via files or pipes or command line args?

http://stiglerdiet.com/blog/2015/Nov/24/my-python-environment-workflow-with-conda/

Code profiling
--------------

https://zapier.com/engineering/profiling-python-boss/


Decorators
----------

http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/

Docs
----

Sphinx has autodoc extension that can create docs from code based docstrings. In addition to rst style, Sphinx
has an extension called Napolean that can translate both Google and Numpy Style docstrings into rst that autodoc
can then use. I mostly seem to be seeing Numpy style out there and that's what I've unknowingly been using. So,
Numpy style it is.

http://sphinx-doc.org/ext/example_numpy.html#example-numpy

http://matplotlib.org/sampledoc/index.html

mailing list?

GitHub page is NOT a project website. NEED a project website.

Packaging and distributing
--------------------------

https://mail.python.org/pipermail/distutils-sig/2014-December/025484.html

http://python-packaging-user-guide.readthedocs.org/en/latest/science/

Do I need a MANIFEST.in file? Perhaps it would help with packaging data. See https://github.com/pypa/sampleproject/blob/master/MANIFEST.in

Nice newbie tutorial on packaging and distribution:
https://tom-christie.github.io/articles/pypi/



The README
----------

At the root of every project, you need a file called README. This plain text file should include at least these bits of information:

Your project summary paragraph
The author’s name and email address
The URL of the project website, if there is one
The URL of the project hosting page (GitHub, etc.)
Where to find the project bug/issue tracker
Where to find the project mailing list


Conda
^^^^^

http://technicaldiscovery.blogspot.com/2013/12/why-i-promote-conda.html

https://www.continuum.io/content/python-3-support-anaconda

https://groups.google.com/a/continuum.io/forum/#!topic/anaconda/z1hX-NLgQhM

 - conda local build and install question answered by Oliphant

Conda build command has option to specify which Python version(s) to build against:

--python PYTHON_VER
              Set the Python version used by conda build. Can be passed multi‐
              ple  times  to  build against multiple versions. Can be 'all' to
              build against all known versions (['2.6', '2.7',  '3.3',  '3.4',
              '3.5'])

Remember to run conda convert to create win-64 or other versions
