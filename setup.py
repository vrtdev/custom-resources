"""Packaging configuration."""
import os

from setuptools import setup, find_packages

with open(os.path.abspath('VERSION.txt'), 'r') as fd:
    VERSION = fd.read().strip()

setup(
    name='custom_resources',
    version=VERSION,
    description='Custom resources for Troposphere/CloudFormation.',
    url='',
    author='VRT DPC',
    author_email='dpc@vrt.be',
    license='',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='cloudformation aws',
    packages=['custom_resources'],
    data_files=['VERSION.txt'],
    install_requires=['troposphere', 'six'],
)
