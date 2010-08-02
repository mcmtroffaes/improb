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

"""Coherent lower probabilities."""

from improb import PSpace, Gamble, Event
from improb.lowprev.lowpoly import LowPoly

class LowProb(LowPoly):
    """Coherent lower probability."""

    def _make_key(self, key):
        gamble, event = LowPoly._make_key(self, key)
        if set(gamble.itervalues()) != set([0, 1]):
            raise ValueError('not an indicator gamble')
        return gamble, event

    def _make_value(self, value):
        lprev, uprev = LowPoly._make_value(self, value)
        if uprev is not None:
            raise ValueError('cannot specify upper prevision')
        return lprev, uprev
