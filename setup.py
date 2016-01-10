
# Copyright 2015 Mark Isken
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup

setup(name='hillmaker',
      version='0.1.0',
      description='Python based occupancy analysis tool',
      author='Mark Isken',
      author_email='isken@oakland.edu',
      url='http://github.com/misken/hillmaker/',
      packages=['hillmaker'],
      package_data={'hillmaker': ['data/*.csv']},
      platforms='any',
      classifiers = [
        'Programming Language :: Python :: 3 :: Only',
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Healthcare Industry',
        'License :: OSI Approved',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Information Analysis',
        ]
     )
