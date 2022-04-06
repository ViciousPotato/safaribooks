"""Safaribooks

Downloads Safari Book Online books using scrapy. Can optionally convert them to .mobi if `kindlegen` is found in PATH.
"""
from setuptools import setup, find_packages

setup(
    name='safaribooks',
    version='0.1.1',
    description='Downloads and converts Safari Book Online books',
    long_description=__doc__,
    packages=find_packages(),
    package_data={
        'safaribooks': [
            'data/mimetype',
            'data/META-INF/container.xml',
            'data/OEBPS/content.opf',
            'data/OEBPS/toc.ncx',
        ],
    },
    install_requires=[
        'scrapy>=1.4.0',
        'twisted==22.2.0',
        'jinja2',
        'beautifulsoup4',
    ],
    entry_points={
        'console_scripts': {
            'safaribooks = safaribooks.__main__:main',
        },
    },
    url='https://github.com/ViciousPotato/safaribooks',
    license='BSD',
    platforms='any',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
