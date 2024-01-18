# Copyright 2023 Mark Isken

#
from setuptools import find_packages, setup

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(name='hillmaker',
      version='0.8.1',
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
          'Programming Language :: Python :: 3.10 ',
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
          'console_scripts': ['hillmaker=hillmaker.console:main'],
      },
      project_urls={
          'Source': 'http://github.com/misken/hillmaker',
          'Examples': 'https://github.com/misken/hillmaker-examples',
      }, 
      install_requires=['pandas>=2.0.0', 'numpy>=1.22', 'tomli>=2.0.1', 'matplotlib>=3.7.1', 'pydantic>=2.1.1', 'seaborn>=0.12.2', 'Jinja2', 'ipykernel']
      )
