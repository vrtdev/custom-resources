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
        'Programming Language :: Python :: 2.7',
        # Troposhere does not support python 3.6 at this time.
        # 'Programming Language :: Python :: 3.6',
    ],
    keywords='cloudformation aws',
    packages=['custom_resources'],
    data_files=['VERSION.txt'],
    install_requires=['troposphere', 'six'],
)
