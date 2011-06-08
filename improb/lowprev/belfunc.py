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

"""Belief functions."""

from __future__ import division, absolute_import, print_function

from improb import PSpace, Gamble, Event
from improb.lowprev.lowprob import LowProb

class BelFunc(LowProb):
    """A belief function, implemented as a
    :class:`~improb.lowprev.lowprob.LowProb`, except that it uses the
    Mobius transform to calculate the natural extension; see
    :meth:`get_lower`.

    .. seealso::

        :meth:`improb.lowprev.lowprob.LowProb.is_completely_monotone`
            To check for complete monotonicity.
    """

    def get_lower(self, gamble, event=True, algorithm='mobius'):
        r"""Calculate the lower expectation of a gamble.

        The default algorithm is to use the Mobius transform :math:`m`
        of the lower probability :math:`\underline{P}`:

        .. seealso::

            :meth:`improb.setfunction.SetFunction.get_bba_choquet`
                Find Choquet integral via Mobius transform of an
                arbitrary set function.

        .. warning::

           To use the Mobius transform, the domain of the lower probability
           must contain *all* events. If needed, call
           :meth:`~improb.lowprev.lowpoly.LowPoly.extend`:

           >>> bel = BelFunc(2, lprob=['0.2', '0.25']) # doctest: +ELLIPSIS
           >>> print(bel)
           0   : 1/5
             1 : 1/4
           >>> bel.get_lower([1, 3]) # oops! fails... # doctest: +ELLIPSIS
           Traceback (most recent call last):
               ...
           KeyError: ...
           >>> # solve linear program instead of trying Mobius transform
           >>> bel.get_lower([1, 3], algorithm='linprog') # 1 * 0.75 + 3 * 0.25 = 1.5
           Fraction(3, 2)
           >>> bel.extend()
           >>> print(bel)
               : 0
           0   : 1/5
             1 : 1/4
           0 1 : 1
           >>> # now try with Mobius transform; should give same result
           >>> bel.get_lower([1, 3]) # now it works
           Fraction(3, 2)

        .. warning::

           With the Mobius algorithm, this method will *not* raise an
           exception even if the assessments are not completely
           monotone, or even incoherent---the Mobius transform is in
           such case still defined, although some of the values of
           :math:`m` will be negative. In fact, if the assessments are
           not 2-monotone, then :math:`\underline{E}` will be
           incoherent as well.

           >>> bel = BelFunc(
           ...     pspace='abcd',
           ...     lprob={'ab': '0.2', 'bc': '0.2', 'abc': '0.2', 'b': '0.1'})
           >>> bel.extend()
           >>> bel.is_n_monotone(2)
           False
           >>> # exact linear programming algorithm
           >>> bel.get_lower([1, 2, 1, 0], algorithm='linprog')
           Fraction(2, 5)
           >>> # mobius algorithm: different result!!
           >>> bel.get_lower([1, 2, 1, 0])
           Fraction(3, 10)

        >>> from improb.lowprev.belfunc import BelFunc
        >>> from improb.lowprev.lowprob import LowProb
        >>> from improb import PSpace
        >>> pspace = PSpace(2)
        >>> lowprob = LowProb(pspace, lprob=['0.3', '0.2'])
        >>> lowprob.extend()
        >>> lowprob.is_completely_monotone()
        True
        >>> print(lowprob)
            : 0
        0   : 3/10
          1 : 1/5
        0 1 : 1
        >>> print(lowprob.mobius)
            : 0
        0   : 3/10
          1 : 1/5
        0 1 : 1/2
        >>> lpr = BelFunc(pspace, bba=lowprob.mobius)
        >>> lpr.is_completely_monotone()
        True
        >>> print(lpr)
            : 0
        0   : 3/10
          1 : 1/5
        0 1 : 1
        >>> print(lpr.mobius)
            : 0
        0   : 3/10
          1 : 1/5
        0 1 : 1/2
        >>> print(lpr.get_lower([1,0]))
        3/10
        >>> print(lpr.get_lower([0,1]))
        1/5
        >>> print(lpr.get_lower([4,9])) # 0.8 * 4 + 0.2 * 9
        5
        >>> print(lpr.get_lower([5,1])) # 0.3 * 5 + 0.7 * 1
        11/5
        """
        # default algorithm
        if algorithm is None:
            algorithm = 'mobius'
        # other algorithm?
        if algorithm != 'mobius':
            return LowProb.get_lower(self, gamble, event, algorithm)
        # do Mobius transform, and calculate lower expectation
        if event is not True:
            raise NotImplementedError
        return self.mobius.get_bba_choquet(gamble)
