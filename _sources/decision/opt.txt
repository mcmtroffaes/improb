.. testsetup::

   from improb import PSpace, Gamble, Event
   from improb.lowprev.lowpoly import LowPoly
   from improb.lowprev.prob import Prob
   from improb.decision.opt import OptAdmissible, OptLowPrevMax, OptLowPrevMaxMin, OptLowPrevMaxMax, OptLowPrevMaxHurwicz, OptLowPrevMaxInterval

.. module:: improb.decision.opt

Optimality Operators
====================

Abstract Operators
------------------

.. autoclass:: Opt
   :members:

.. autoclass:: OptPartialPreorder
   :show-inheritance:
   :members:

.. autoclass:: OptTotalPreorder
   :show-inheritance:
   :members:

Concrete Operators
------------------

.. autoclass:: OptAdmissible
   :show-inheritance:
   :members:

.. autoclass:: OptLowPrevMax
   :show-inheritance:
   :members:

.. autoclass:: OptLowPrevMaxMin
   :show-inheritance:
   :members:

.. autoclass:: OptLowPrevMaxMax
   :show-inheritance:
   :members:

.. autoclass:: OptLowPrevMaxHurwicz
   :show-inheritance:
   :members:

.. autoclass:: OptLowPrevMaxInterval
   :show-inheritance:
   :members:

Examples
--------

Example taken from [#troffaes2007]_:

>>> lpr = LowPoly(pspace=2)
>>> lpr.set_lower([1, 0], 0.28)
>>> lpr.set_upper([1, 0], 0.70)
>>> gambles = [[4, 0], [0, 4], [3, 2], [0.5, 3], [2.35, 2.35], [4.1, -0.3]]
>>> opt = OptLowPrevMax(lpr)
>>> list(opt(gambles)) == [[4, 0], [0, 4], [3, 2], [2.35, 2.35]]
True
>>> list(OptLowPrevMaxMin(lpr)(gambles)) == [[2.35, 2.35]]
True
>>> list(OptLowPrevMaxMax(lpr)(gambles)) == [[0, 4]]
True
>>> list(OptLowPrevMaxInterval(lpr)(gambles)) == [[4, 0], [0, 4], [3, 2], [2.35, 2.35], [4.1, -0.3]]
True

Another example:

>>> lpr = Prob(pspace=4, prob=[0.42, 0.08, 0.18, 0.32]).get_linvac(0.1)
>>> opt = OptLowPrevMax(lpr)
>>> for c in range(3):
...     gambles = [[10-c,10-c,15-c,15-c],[10-c,5-c,15-c,20-c],
...                [5-c,10-c,20-c,15-c],[5-c,5-c,20-c,20-c],
...                [10,10,15,15],[5,5,20,20]]
...     print(list(opt(gambles)))
[[10, 5, 15, 20]]
[[9, 4, 14, 19], [10, 10, 15, 15], [5, 5, 20, 20]]
[[10, 10, 15, 15], [5, 5, 20, 20]]


.. rubric:: Footnotes

.. [#troffaes2007]

    Matthias C. M. Troffaes. Decision making under uncertainty using
    imprecise probabilities. International Journal of Approximate
    Reasoning, 45(1):17-29, May 2007.
