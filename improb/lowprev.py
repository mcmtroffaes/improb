# improb is a Python module for working with imprecise probabilities
# Copyright (c) 2008, Matthias Troffaes
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

"""A module for working with lower previsions."""

import pycddlib

class LowPrev:
    """A class for lower previsions.

    This class implements a lower prevision as a sequence of half-spaces.
    These half-spaces constrain a convex set of probability mass functions.
    Each half-space is represented by a gamble, and a number (i.e. its lower
    expectation/prevision).

    Add half-space constraints by calling for instance the
    L{set_lower} and L{set_upper} functions. Calculate the natural extension
    with the L{get_lower} and L{get_upper} functions.

    Example
    =======

    >>> import lowprev
    >>> lpr = lowprev.LowPrev(4)
    >>> lpr.set_lower([4,2,1,0], 3)
    >>> lpr.set_upper([4,1,2,0], 3)
    >>> lpr.is_avoiding_sure_loss()
    True
    >>> lpr.is_coherent()
    True
    >>> lpr.is_linear()
    False
    >>> print "%.6f" % lpr.get_lower([1,0,0,0])
    0.500000
    >>> print "%.6f" % lpr.get_upper([1,0,0,0])
    0.750000
    >>> list(lpr)
    [([4.0, 2.0, 1.0, 0.0], 3.0), ([-4.0, -1.0, -2.0, 0.0], -3.0)]
    >>> lpr.get_maximal_gambles([[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]])
    [[1, 0, 0, 0], [0, 1, 0, 0]]
    >>> lpr.get_maximal_gambles([[0,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]])
    [[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    """

    def __init__(self, numstates = 2):
        """Construct vacuous lower prevision on possibility space of given
        size.

        @param numstates: The number of states.
        @type numstates: int
        """
        self._numstates = numstates
        self._matrix = pycddlib.Matrix([[+1] + [-1] * numstates,
                                        [-1] + [+1] * numstates]
                                        +
                                        [[0] + [1 if i == j else 0
                                                for i in xrange(numstates)]
                                         for j in xrange(numstates)])

    def set_lower(self, gamble, lprev):
        """Constrain the expectation of C{gamble} to be at least C{lprev}.

        @param gamble: The gamble whose expectation to bound.
        @type gamble: list of floats/ints
        @param lprev: The lower bound for this expectation.
        @type lprev: float/int
        """
        self._matrix.append_rows([[-lprev] + gamble])

    def set_upper(self, gamble, uprev):
        """Constrain the expectation of C{gamble} to be at most C{uprev}.

        @param gamble: The gamble whose expectation to bound.
        @type gamble: list of floats/ints
        @param uprev: The upper bound for this expectation.
        @type uprev: float/int
        """
        self._matrix.append_rows([[uprev] + [-value for value in gamble]])

    def set_precise(self, gamble, prev):
        """Constrain the expectation of C{gamble} to be exactly C{prev}.

        @param gamble: The gamble whose expectation to bound.
        @type gamble: list of floats/ints
        @param prev: The precise bound for this expectation.
        @type prev: float/int
        """
        self.set_lower(gamble, prev)
        self.set_upper(gamble, prev)

    def __iter__(self):
        """Yield tuples (gamble, lprev)."""
        for rownum in xrange(self._numstates + 2, self._matrix.rowsize):
            row = self._matrix[rownum]
            yield row[1:], -row[0]

    def get_lower(self, gamble):
        """Return the lower expectation for C{gamble} via natural extension.

        @param gamble: The gamble whose lower expectation to find.
        @type gamble: list of floats/ints
        @return: The lower bound for this expectation, i.e. the natural
            extension of the gamble.
        """
        self._matrix.set_lp_obj_type(pycddlib.LPOBJ_MIN)
        self._matrix.set_lp_obj_func([0] + gamble)
        #print self._matrix # DEBUG
        linprog = pycddlib.LinProg(self._matrix)
        linprog.solve()
        #print linprog # DEBUG
        if linprog.status == pycddlib.LPSTATUS_OPTIMAL:
            return linprog.opt_value
        elif linprog.status == pycddlib.LPSTATUS_INCONSISTENT:
            raise ValueError("lower prevision incurs sure loss")
        else:
            raise RuntimeError("BUG: unexpected status (%i)" % linprog.status)

    def get_upper(self, gamble):
        """Return the upper expectation for C{gamble} via natural extension.

        @param gamble: The gamble whose upper expectation to find.
        @type gamble: list of floats/ints
        @return: The upper bound for this expectation, i.e. the natural
            extension of the gamble.
        """
        return -self.get_lower([-value for value in gamble])

    #def getcredalset(self):
    #    """Find credal set corresponding to this lower prevision."""
    #    raise NotImplementedError

    def is_avoiding_sure_loss(self):
        """No Dutch book? Does the lower prevision avoid sure loss?

        @return: C{True} if the lower prevision avoids sure loss, C{False}
            otherwise.
        """
        try:
            self.get_lower([0] * self._numstates)
        except ValueError:
            return False
        return True

    def is_coherent(self, tolerance=1e-6):
        """Do all assessments coincide with their natural extension? Is the
        lower prevision coherent?"""
        # first check if we are avoiding sure loss
        if not self.is_avoiding_sure_loss():
            return False
        # we're avoiding sure loss, so check the natural extension
        for gamble, lprev in self:
            if self.get_lower(gamble) > lprev + tolerance:
                return False
        return True

    def is_linear(self, tolerance=1e-6):
        """Is the lower prevision a linear prevision? More precisely,
        we check that the natural extension is linear on the linear
        span of the domain of the lower prevision.
        """
        # first check if we are avoiding sure loss
        if not self.is_avoiding_sure_loss():
            return False
        # we're avoiding sure loss, so check the natural extension
        for gamble, lprev in self:
            # implementation note: if upper - lower <= tolerance then
            # obviously lprev is within tolerance of the lower and the
            # upper as well, so we can keep lprev out of the picture
            # when checking for linearity (of course, it's taken into
            # account when calculating the natural extension)
            if self.get_upper(gamble) - self.get_lower(gamble) > tolerance:
                return False
        return True

    def get_maximal_gambles(self, gambles, tolerance=1e-6):
        """Return a list of maximal gambles."""
        # TODO make this more efficient
        maximal = []
        gambles = list(gambles)
        for gamble in gambles:
            for other_gamble in gambles:
                if (self.get_lower(
                    [y - x for x, y in zip(gamble, other_gamble)])
                    > tolerance):
                    # gamble cannot be maximal, it is dominated by other_gamble
                    break
                if (all(y >= x for  x, y in zip(gamble, other_gamble))
                    and any(y > x + tolerance
                            for x, y in zip(gamble, other_gamble))):
                    # pointwise dominance
                    break
            else:
                # gamble not dominated by any gamble, so it is maximal
                maximal.append(gamble)
        return maximal

    #def optimize(self):
    #    """Removes redundant assessments."""
    #    raise NotImplementedError

    #def __cmp__(self, lowprev):
    #    """Compares two lower previsions, checking for dominance."""
    #    raise NotImplementedError

    #def __iand__(self, lowprev):
    #    """Conjunction. Result is not necessarily coherent, and incurs sure
    #    loss if conjunction does not exist."""
    #    raise NotImplementedError

    #def __ior__(self, lowprev):
    #    """Disjunction (unanimity rule). Result is not necessarily
    #    coherent."""
    #    raise NotImplementedError
