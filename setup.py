from setuptools import setup, find_packages
import sys, os

version = '0.2'

setup(
    name='ckanext-oaks',
    version=version,
    description="Open Architecture Knowledge System",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='graffio',
    author_email='graffio@lynxlab.com',
    url='http://lynxlab.com',
    license='GPL 3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.oaks'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        # Add plugins here, e.g.
        oaksPlugin=ckanext.oaks.plugin:oaksPlugin
    ''',
)
