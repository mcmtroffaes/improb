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

"""Tests for imprecise Markov chains."""

from improb import Gamble
from improb.markovchain.discrete import (
    iterate_lower_transition_operator,
    apply_lower_transition_operators,
    )
import numpy as np  # TODO get rid of numpy dependency


def test_iterate_lower_transition_operator():

    def get_lower_expectation_0(func):
        return 0.5 * min(func[0], func[1]) + 0.5 * (0.5 * func[0] + 0.5 * func[1])

    def get_lower_expectation_1(func):
        return 0.2 * min(func[0], func[1]) + 0.8 * (0.3 * func[0] + 0.7 * func[1])

    lower_transition_operator = {
        0: get_lower_expectation_0, 1: get_lower_expectation_1}

    func = Gamble(2, (1, 2))

    # 0: 0.5 * 1 + 0.5 * 1.5 = 1.25
    # 1: 0.2 * 1 + 0.8 * (0.3 + 1.4) = 1.56

    # 0: 0.5 * 1.25 + 0.5 * 1.405 = 1.3275
    # 1: 0.2 * 1.25 + 0.8 * (0.3 * 1.25 + 0.7 * 1.56) = 1.4236

    it = iterate_lower_transition_operator(
        lower_transition_operator, func)

    np.testing.assert_allclose(next(it), (1., 2.))
    np.testing.assert_allclose(next(it), (1.25, 1.56))
    np.testing.assert_allclose(next(it), (1.3275, 1.4236))

def test_apply_lower_transition_operators():

    import numpy as np

    def get_lower_expectation_0(func):
        return 0.5 * func[0] + 0.5 * func[1]

    def get_lower_expectation_1(func):
        return 0.3 * func[0] + 0.7 * func[1]

    # lower_transition_operators_1 is
    #
    #                 --- 0.3 --- 0
    #    -- 0.5 --- 0 |
    #   /             --- 0.7 --- 1
    # 0 
    #   \             --- 0.5 --- 0
    #    -- 0.5 --- 1 |
    #                 --- 0.5 --- 1
    #
    #                 --- 0.3 --- 0
    #    -- 0.3 --- 0 |
    #   /             --- 0.7 --- 1
    # 1 
    #   \             --- 0.5 --- 0
    #    -- 0.7 --- 1 |
    #                 --- 0.5 --- 1

    # For example, starting from state 0, the probability of being in
    # state 0 after two time steps is 0.5*0.3 + 0.5*0.5 = 0.4;
    # starting from state 1, prob of state 0 is 0.3*0.3 + 0.7*0.5 =
    # 0.44

    lower_transition_operators_1 = [
        # state 0               , state 1
        {0: get_lower_expectation_0, 1: get_lower_expectation_1}, # time step 1
        {0: get_lower_expectation_1, 1: get_lower_expectation_0}, # time step 2
        ]

    # lower_transition_operators_2 is
    #
    #                 --- 0.5 --- 0
    #    -- 0.3 --- 0 |
    #   /             --- 0.5 --- 1
    # 0 
    #   \             --- 0.3 --- 0
    #    -- 0.7 --- 1 |
    #                 --- 0.7 --- 1
    #
    #                 --- 0.5 --- 0
    #    -- 0.5 --- 0 |
    #   /             --- 0.5 --- 1
    # 1 
    #   \             --- 0.3 --- 0
    #    -- 0.5 --- 1 |
    #                 --- 0.7 --- 1

    # For example, starting from state 0, the probability of being in
    # state 0 after two time steps is 0.3*0.5 + 0.7*0.3 = 0.36;
    # starting from state 1, prob of state 0 is 0.5*0.5 + 0.5*0.3 =
    # 0.4

    lower_transition_operators_2 = [
        {0: get_lower_expectation_1, 1: get_lower_expectation_0},
        {0: get_lower_expectation_0, 1: get_lower_expectation_1},
        ]

    # find the probability of being in state 0 after two time steps

    func = Gamble(2, (1, 0))

    func21 = apply_lower_transition_operators(
        lower_transition_operators_1, func)

    func22 = apply_lower_transition_operators(
        lower_transition_operators_2, func)

    np.testing.assert_allclose(func21, (0.4, 0.44))
    np.testing.assert_allclose(func22, (0.36, 0.4))
