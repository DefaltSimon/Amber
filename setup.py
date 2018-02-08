# coding=utf-8
from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='Amber',
      version='0.1.1',
      description='Text Adventure interpreter',
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.5',
          'Intended Audience :: Developers',
      ],
      url='https://github.com/DefaltSimon/Amber',
      author='DefaltSimon',
      license='MIT',
      keywords="defaltsimon amber text adventure",
      packages=['amber'],
      install_requires=requirements,
      zip_safe=True)
