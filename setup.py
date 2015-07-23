

from setuptools import setup

setup(name='hillmaker',
      version='0.1',
      description='Python based hillmaker',
      author='Mark Isken',
      author_email='isken@oakland.edu',
      url='http://github.com/misken/hillmaker/',
      packages=['hillmaker'],
      platforms='any',
      classifiers = [
        'Programming Language :: Python :: 3 :: Only',
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Healthcare Industry',
        'License :: OSI Approved :: TBD',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Information Analysis',
        ]
     )


"""
distutils approach

#from distutils.core import setup
scripts = ['scripts/mwts'],
"""

#setup(
    #name='sandman',
    #version=sandman.__version__,
    #url='http://github.com/jeffknupp/sandman/',
    #license='Apache Software License',
    #author='Jeff Knupp',
    #tests_require=['pytest'],
    #install_requires=['Flask>=0.10.1',
                    #'Flask-SQLAlchemy>=1.0',
                    #'SQLAlchemy==0.8.2',
                    #],
    #cmdclass={'test': PyTest},
    #author_email='jeff@jeffknupp.com',
    #description='Automated REST APIs for existing database-driven systems',
    #long_description=long_description,
    #packages=['sandman'],
    #include_package_data=True,
    #platforms='any',
    #test_suite='sandman.test.test_sandman',
    #classifiers = [
        #'Programming Language :: Python',
        #'Development Status :: 4 - Beta',
        #'Natural Language :: English',
        #'Environment :: Web Environment',
        #'Intended Audience :: Developers',
        #'License :: OSI Approved :: Apache Software License',
        #'Operating System :: OS Independent',
        #'Topic :: Software Development :: Libraries :: Python Modules',
        #'Topic :: Software Development :: Libraries :: Application Frameworks',
        #'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        #],
    #extras_require={
        #'testing': ['pytest'],
    #}
##
##
##
)
