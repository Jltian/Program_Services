#! /usr/bin/env python
#
# A setuptools based setup module. See: https://packaging.python.org/en/latest/distributing.html
#
# Always prefer setuptools over distutils

import re
import os
import codecs

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    intentionally *not* adding an encoding option to open
    see: https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    :param parts:
    :return:
    """
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# Get the long description from the README file
with codecs.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='jetend',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=find_version('jetend', '__init__.py'),

    description='',
    long_description=long_description,

    url='',

    # Author details
    author='Mingo',
    author_email='tangming@jiumingfunds.com',

    # Choose your license
    license='GNU GENERAL PUBLIC LICENSE',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # 'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.5',
        # 'Programming Language :: Python :: 3.6',
        # 'Programming Language :: Python :: 3.7',
    ],

    # What does your project relate to?
    keywords='jiuming funds extended modules',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['samples']),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    # py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'docopt>=0.6.2',
        # 'jieba>=0.38',      # basic splitting engine
        # 'pandas>=0.20',     # data frame package
        # 'openpyxl>=2.4.0'   # Excel writing engine
    ],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    # extras_require={
    #     'data': ['check-manifest'],
    #     'test': ['tests_require'],
    # },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # package_data={
    #     'data': ['*.csv', 'DeveloperDefinedAdjustment.txt'],
    # },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[  # (
    #     # 'data', [
    #     #     'data/DeveloperDefinedAdjustment.txt',
    #     #     'data/PackageDefinedFirmTypeWhitelist.xlsx',
    #     #     'data/PackageDefinedKeywordBlacklist.xlsx',
    #     #     'data/PackageDefinedPartitionExpression.xlsx',
    #     #     'data/PackageDefinedServiceTypeWhitelist.xlsx',
    #     #     'data/ToponymInfomation.xlsx'
    #     # ]),
    #     ('.', ['README.md', ]), ],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    # entry_points=dict(console_scripts=['pip=pip:main',
    #                                    'pip%s=pip:main' % sys.version[:1],
    #                                    'pip%s=pip:main' % sys.version[:3]]),
    entry_points={
        'console_scripts': [
            'socketer=jetend.CMD:entry_socketer',
        ],
    },
)
