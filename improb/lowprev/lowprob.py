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
from improb.lowprev import LowPrev

# TODO restrict assignment to events

class LowProb(LowPrev):
    """Coherent lower probability."""
    def __init__(self, pspace, mapping):
        """Construct a lower probability on the power set of the given
        possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param mapping: A mapping that defines the value on each event (missing values default to zero).
        :type mapping: :class:`collections.Mapping <collections>`
        """
        SetFunction.__init__(self, pspace, mapping)
        self._lpr = LowPrev(self.pspace)
        for event, value in self:
            if value > 0:
                self._lpr.set_lower(event, value)

    def get_lower(self, gamble, event=None, tolerance=1e-6):
        self._lpr.get_lower(gamble, event, tolerance)

    def get_upper(self, gamble, event=None, tolerance=1e-6):
        self._lpr.get_upper(gamble, event, tolerance)
