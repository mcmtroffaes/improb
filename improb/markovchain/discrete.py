# improb is a Python module for working with imprecise probabilities
# Copyright (c) 2008-2014, Matthias Troffaes
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

"""Discrete time imprecise Markov chains."""

from improb import Gamble


# A lower transition operator is simply a list of lower expectation operators
# on gambles on states, one such lower expectation operator for each state.

def apply_lower_transition_operator(lower_transition_operator, func):
    """Apply a lower transition operator on the given function."""
    return Gamble(
        pspace=func.pspace,
        data={
            omega: get_lower_expectation(func)
            for omega, get_lower_expectation
            in lower_transition_operator.iteritems()
            },
        )

def iterate_lower_transition_operator(lower_transition_operator, func):
    """Repeatedly apply a lower transition operator on the given function."""
    while True:
        yield func
        nextfunc = apply_lower_transition_operator(
            lower_transition_operator, func)
        func = nextfunc

def apply_lower_transition_operators(lower_transition_operators, func):
    """Apply all lower transition operators. This covers the
    non-stationary case.
    """
    if not lower_transition_operators:
        return func
    else:
        return apply_lower_transition_operators(
            lower_transition_operators[:-1],
            apply_lower_transition_operator(
                lower_transition_operators[-1], func))

def iterate_lower_transition_operators(lower_transition_operators, func):
    """Apply lower transition operators for each time step. This also
    covers the non-stationary case.
    """
    for n in xrange(len(lower_transition_operators) + 1):
        yield apply_lower_transition_operators(
            lower_transition_operators[:n], func)
