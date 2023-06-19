# Copyright 2022 Mark Isken
#

from setuptools import find_packages, setup

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(name='hillmaker',
      version='0.4.5',
      description='Occupancy analysis tool for systems having time of day and day of week effects',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='Mark Isken',
      author_email='isken@oakland.edu',
      url='http://github.com/misken/hillmaker/',
      packages=find_packages("src"),
      package_dir={"": "src"},
      platforms='any',
      classifiers=[
          'Programming Language :: Python :: 3 ',
          'Programming Language :: Python :: 3.8 ',
          'Development Status :: 4 - Beta',
          'Natural Language :: English',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Healthcare Industry',
          'License :: OSI Approved',
          'Operating System :: OS Independent',
          'Topic :: Scientific/Engineering :: Information Analysis',
      ],
      entry_points={
          'console_scripts': ['hillmaker=hillmaker.hills:main'],
      },
      project_urls={
          'Source': 'http://github.com/misken/hillmaker',
          'Examples': 'https://github.com/misken/hillmaker-examples',
      }, install_requires=['pandas>=1.4.0', 'numpy>=1.22'],
      python_requires='>=3.9'
      )
