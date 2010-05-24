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
    L{setlower} and L{setupper} functions. Calculate the natural extension
    with the L{getlower} and L{getupper} functions.

    Example
    =======

    >>> import lowprev
    >>> lpr = lowprev.LowPrev(4)
    >>> lpr.setlower([4,2,1,0], 3)
    >>> lpr.setupper([4,1,2,0], 3)
    >>> lpr.isavoidingsureloss()
    True
    >>> print "%.6f" % lpr.getlower([1,0,0,0])
    0.500000
    >>> print "%.6f" % lpr.getupper([1,0,0,0])
    0.750000
    >>> list(lpr)
    [([4.0, 2.0, 1.0, 0.0], -3.0), ([-4.0, -1.0, -2.0, 0.0], 3.0)]
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

    def setlower(self, gamble, lprev):
        """Constrain the expectation of C{gamble} to be at least C{lprev}.

        @param gamble: The gamble whose expectation to bound.
        @type gamble: list of floats/ints
        @param lprev: The lower bound for this expectation.
        @type lprev: float/int
        """
        self._matrix.append_rows([[-lprev] + gamble])

    def setupper(self, gamble, uprev):
        """Constrain the expectation of C{gamble} to be at most C{uprev}.

        @param gamble: The gamble whose expectation to bound.
        @type gamble: list of floats/ints
        @param uprev: The upper bound for this expectation.
        @type uprev: float/int
        """
        self._matrix.append_rows([[uprev] + [-value for value in gamble]])

    def setprecise(self, gamble, prev):
        """Constrain the expectation of C{gamble} to be exactly C{prev}.

        @param gamble: The gamble whose expectation to bound.
        @type gamble: list of floats/ints
        @param prev: The precise bound for this expectation.
        @type prev: float/int
        """
        self.setlower(gamble, prev)
        self.setupper(gamble, prev)

    def __iter__(self):
        """Yield tuples (gamble, lprev)."""
        for rownum in xrange(self._numstates + 2, self._matrix.rowsize):
            row = self._matrix[rownum]
            yield row[1:], row[0]

    def getlower(self, gamble):
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

    def getupper(self, gamble):
        """Return the upper expectation for C{gamble} via natural extension.

        @param gamble: The gamble whose upper expectation to find.
        @type gamble: list of floats/ints
        @return: The upper bound for this expectation, i.e. the natural
            extension of the gamble.
        """
        return -self.getlower([-value for value in gamble])

    #def getcredalset(self):
    #    """Find credal set corresponding to this lower prevision."""
    #    raise NotImplementedError

    def isavoidingsureloss(self):
        """No Dutch book? Does the lower prevision avoid sure loss?

        @return: C{True} if the lower prevision avoids sure loss, C{False}
            otherwise.
        """
        try:
            self.getlower([0] * self._numstates)
        except ValueError:
            return False
        return True

    #def iscoherent(self):
    #    """Do all assessments coincide with their natural extension? Is the
    #    lower prevision coherent?"""
    #    raise NotImplementedError

    #def islinear(self):
    #    """Is the lower prevision a linear prevision?"""
    #    raise NotImplementedError

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
