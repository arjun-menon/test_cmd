#!/usr/bin/env python

from setuptools import setup

setup(name='test_cmd',
      version='1.0',
      description='Tool for black-box testing command-line programs using STDIN, STDOUT and STDERR',
      long_description=open('README.rst').read(),
      url='https://github.com/arjun-menon/test_cmd',
      author='Arjun G. Menon',
      author_email='contact@arjungmenon.com',
      keywords='command line terminal functional black box testing arguments stdin stdout stderr',
      license='Apache',
      py_modules=['test_cmd'],
      entry_points = {
        'console_scripts': ['test_cmd=test_cmd:main'],
      },
      classifiers=[
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: Apache Software License',
        'Environment :: Console'
      ])
