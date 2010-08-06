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
    """This identical to :class:`~improb.lowprev.lowprob.LowProb`,
    except that it uses the Mobius inverse to calculate the natural
    extension.
    """

    def get_lower(self, gamble, event=True):
        r"""Calculate the lower expectation of a gamble by the
        following formula:

        .. math::

           \underline{E}(f)=
           \sum_{A\subseteq\Omega}
           m(A)\inf_{\omega\in A}f(\omega)

        where :math:`m` is the Mobius inverse of the lower probability
        :math:`\underline{P}`.

        .. seealso::

            :meth:`improb.setfunction.SetFunction.get_mobius_inverse`
                Mobius inverse calculation of an arbitrary set function.

        This method will *not* raise an exception even if the
        assessments are not completely monotone, or even
        incoherent---the Mobius inverse is in such case still defined,
        although some of the values of :math:`m` will be negative
        (obviously, in such case, :math:`\underline{E}` will be
        incoherent as well).

        >>> from improb.lowprev.belfunc import BelFunc
        >>> from improb.lowprev.lowprob import LowProb
        >>> from improb import PSpace
        >>> pspace = PSpace(2)
        >>> lowprob = LowProb(pspace, lprob=['0.3', '0.2'], number_type='fraction')
        >>> lpr = BelFunc(pspace, bba=lowprob.mobius_inverse, number_type='fraction')
        >>> print(lpr.mobius_inverse)
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
        gamble = self.make_gamble(gamble)
        if event is not True:
            raise NotImplementedError
        mobius_inverse = self.mobius_inverse
        return sum(
            (mobius_inverse[event_] * min(gamble[w] for w in event_)
             for event_ in self.pspace.subsets()
             if event_),
            self.make_number(0))
