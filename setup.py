from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='poloniex',

    version='0.6.1',

    description='Poloniex Python API client',
    long_description=long_description,

    # The project's main homepage.
    # url='https://github.com/pypa/sampleproject',

    author='Danijel Pančić',
    author_email='danijel.pancic@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Bitcoin',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    keywords='cryptocurrencies poloniex api',

    packages=find_packages(exclude=['examples', 'tests']),

    install_requires=['requests', 'autobahn[asyncio ]'],
)