#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()


setup(name='deezer-dl',
      version='0.7',
      description='Deezer music downloader',
      author='Lola, Maxime',
      author_email='',
      packages=['deezerdl', 'deezer'],
      package_dir={'deezerdl': 'deezerdl', 'deezer': 'deezerdl/deezer'},
      install_requires=requirements,
      entry_points = {
            'console_scripts': ['deezer-dl=deezerdl.main:main'],
      },
     )