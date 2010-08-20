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

"""A module with utility functions for decision making."""

from __future__ import division, absolute_import, print_function

from improb import PSpace, Event, Gamble

def filter_maximal(set_, dominates, *args):
    """Filter elements that are maximal according to the given
    partial ordering.

    >>> list(filter_maximal([[0,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]], dominates_pointwise))
    [[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    >>> list(filter_maximal([3,2,9,6,16,9.1,16,5.3], lambda x, y: x > y))
    [16, 16]
    >>> list(filter_maximal([set([0,1]), set([1]), set([0]), set([1,2]), set([1,2,3])], lambda x, y: x > y))
    [set([0, 1]), set([1, 2, 3])]
    """
    # keep track of maximal elements
    maximal_elements = []
    # make a stack of all possibly maximal elements
    elements = list(set_)
    while elements:
        # pop a candidate maximal element from the stack
        element = elements.pop(0)
        # compare element against other maximal elements
        for other_element in maximal_elements:
            if dominates(other_element, element, *args):
                # not maximal
                break
        else:
            # compare element against remaining possibly maximal elements
            for other_i, other_element in enumerate(elements):
                if dominates(other_element, element, *args):
                    # not maximal
                    break
            else:
                # we found a maximal one!
                yield element
                maximal_elements.append(element)

def dominates_pointwise(gamble, other_gamble, event=True, tolerance=1e-6):
    """Does gamble dominate other_gamble point-wise?"""
    # XXX we're ignoring the event for now
    return (all(x >= y for  x, y in zip(gamble, other_gamble))
            and any(x > y + tolerance
                    for x, y in zip(gamble, other_gamble)))
