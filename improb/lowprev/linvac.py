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

"""Linear vacuous mixtures."""

from __future__ import division, absolute_import, print_function

from improb import PSpace, Gamble, Event
from improb.lowprev.belfunc import BelFunc

class LinVac(BelFunc):
    """Linear-vacuous mixture, implemented as a
    :class:`~improb.lowprev.belfunc.BelFunc` whose natural extension
    is calculated via a much simpler formula; see :meth:`get_lower`.
    Assessments on non-singletons, and conditional assessments, raise
    a `~exceptions.ValueError`.

    >>> from improb.lowprev.linvac import LinVac
    >>> lpr = LinVac(3, lprob={(0,): '0.2'})
    >>> print(lpr)
    0     : 1/5
    >>> lpr.extend()
    >>> print(lpr)
    0     : 1/5
      1   : 0
        2 : 0

    >>> from improb.lowprev.prob import Prob
    >>> lpr = Prob(3, prob=['0.2', '0.3', '0.5']).get_linvac('0.1')
    >>> print(lpr.get_lower([1,0,0]))
    9/50
    >>> print(lpr.get_lower([0,1,0]))
    27/100
    >>> print(lpr.get_lower([0,0,1]))
    9/20
    >>> print(lpr.get_lower([3,2,1]))
    163/100
    >>> print(lpr.get_upper([3,2,1]))
    183/100
    >>> lpr = Prob(4, prob=['0.42', '0.08', '0.18', '0.32']).get_linvac('0.1')
    >>> print(lpr.get_lower([5,5,-5,-5]))
    -1/2
    >>> print(lpr.get_lower([5,5,-5,-5], set([0,2]))) # (6 - 31 * 0.1) / (3 + 2 * 0.1)
    29/32
    >>> print(lpr.get_lower([-5,-5,5,5], set([1,3]))) # (6 - 31 * 0.1) / (2 + 3 * 0.1) # doctest: +ELLIPSIS
    29/23
    >>> print(lpr.get_lower([0,5,0,-5])) # -(6 + 19 * 0.1) / 5
    -79/50
    >>> print(lpr.get_lower([0,-5,0,5])) # (6 - 31 * 0.1) / 5
    29/50
    """
    def _make_key(self, key):
        gamble, event = BelFunc._make_key(self, key)
        gamble_event = self.pspace.make_event(gamble)
        if not gamble_event.is_singleton():
            raise ValueError('not a singleton')
        if not event.is_true():
            raise ValueError('must be unconditional')
        return gamble, event

    def get_lower(self, gamble, event=True, algorithm='linvac'):
        r"""Calculate the lower expectation of a gamble conditional on
        an event, by the following formula:

        .. math::

           \underline{E}(f|A)=
           \frac{
           (1-\epsilon)\sum_{\omega\in A}p(\omega)f(\omega)
           + \epsilon\min_{\omega\in A}f(\omega)
           }{
           (1-\epsilon)\sum_{\omega\in A}p(\omega)
           + \epsilon
           }

        where :math:`\epsilon=1-\sum_{\omega}\underline{P}(\omega)` and
        :math:`p(\omega)=\underline{P}(\omega)/(1-\epsilon)`. Here,
        :math:`\underline{P}(\omega)` is simply::

            self[{omega: 1}, True][0]

        This method will *not* raise an exception, even if the
        assessments are incoherent (obviously, in such case,
        :math:`\underline{E}` will be incoherent as well). It will
        raise an exception if not all lower probabilities on
        singletons are defined (if needed, extend it first).
        """
        # default algorithm
        if algorithm is None:
            algorithm = 'linvac'
        # other algorithms?
        if algorithm != 'linvac':
            return BelFunc.get_lower(self, gamble, event, algorithm)
        gamble = self.make_gamble(gamble)
        event = self.pspace.make_event(event)
        epsilon = 1 - sum(self[{omega: 1}, True][0] for omega in self.pspace)
        return (
            (sum(self[{omega: 1}, True][0] * gamble[omega] for omega in event)
             + epsilon * min(gamble[omega] for omega in event))
            /
            (sum(self[{omega: 1}, True][0] for omega in event)
             + epsilon)
            )

    def get_extend_domain(self):
        return ((event, True) for event in self.pspace.subsets(size=1))
