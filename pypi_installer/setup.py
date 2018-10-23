"""
Setup file for SBtab Python Modules.
The SBtab modules can be integrated into existing workflows of Systems Biology.
See: https://bitbucket.org/tlubitz/sbtab

"""
import os
from setuptools import setup,find_packages

with open(os.path.join('sbtab', 'VERSION')) as version_file:
    __version__ = version_file.read().strip()

setup(name='sbtab',version=__version__,description='SBtab - Standardised Data Tables for Systems Biology',long_description='SBtab - Standardised Data Tables for Systems Biology',url='https://www.sbtab.net',author='Timo Lubitz',author_email='timo.lubitz@gmail.com',license='MIT',classifiers=['Development Status :: 4 - Beta','Intended Audience :: Developers', 'Topic :: Software Development', 'Programming Language :: Python :: 3.0'],keywords='modelling systems biology standard format data table',packages=find_packages(),install_requires=['python-libsbml','tablib','openpyxl'],python_requires='>=3.0',include_package_data=True)
