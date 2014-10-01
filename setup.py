#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

requirements = [
    'python-novaclient',
    'python-keystoneclient',
    'python-ceilometerclient',
]

setup(
    name='nectar_reporting',
    version='0.1.0',
    description='A collection of NeCTAR reporting scripts',
    long_description=readme + '\n\n' + history,
    author='Russell Sim',
    author_email='russell.sim@gmail.com',
    url='https://github.com/NeCTAR-RC/nectar-reporting',
    packages=[
        'nectar_reporting',
    ],
    package_dir={'nectar_reporting':
                 'nectar_reporting'},
    include_package_data=True,
    install_requires=requirements,
    license="GPLv3+",
    zip_safe=False,
    keywords='nectar_reporting',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: '
        'GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    data_files=[
        ('/etc/nectar', ['reporting.ini']),
    ],
    entry_points={
        'console_scripts':
        ['nectar-report-idle-servers'
         ' = nectar_reporting.report_idle_servers:main']
    },
)
