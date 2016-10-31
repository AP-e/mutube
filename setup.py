from setuptools import setup, find_packages

setup(name='mutube',
      version='0.1',
      description='Scrape YouTube links from 4chan threads.',
      url='https://github.com/AP-e/mutube',
      license='unlicense',
      classifiers=['Development Status :: 2 - Pre-Alpha',
                   'Programming Language :: Python :: 3 :: Only'],
      keywords='4chan youtube',
      packages=find_packages(),
      install_requires=['bs4'])
