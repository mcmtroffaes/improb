"""Setup script for improb."""

# improb is a Python module for working with imprecise probabilities
# Copyright (c) 2008-2010, Matthias Troffaes
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

classifiers = """\
Development Status :: 3 - Alpha
License :: OSI Approved :: GNU General Public License (GPL)
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
Intended Audience :: Science/Research
Topic :: Scientific/Engineering :: Mathematics
Programming Language :: Python
Programming Language :: Python :: 2
Operating System :: OS Independent"""

from setuptools import setup
from improb import __version__

doclines = open('README.rst').read().split('\n')

setup(
    name = "improb",
    version = __version__,
    packages = ['improb', 'improb.lowprev', 'improb.decision'],
    author = "Matthias Troffaes",
    author_email = "matthias.troffaes@gmail.com",
    license = "GPL",
    keywords = "statistics, lower prevision, imprecise probability, credal set",
    platforms = "any",
    description = doclines[0],
    long_description = "\n".join(doclines[2:]),
    url = "http://pypi.python.org/pypi/improb/",
    classifiers = classifiers.split('\n'),
)
