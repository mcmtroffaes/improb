Lower Previsions
================

.. currentmodule:: improb.lowprev

.. autoclass:: LowPrev
   :members:

Examples
--------

>>> import lowprev
>>> import decision
>>> lpr = lowprev.LowPrev(4)
>>> lpr.set_lower([4,2,1,0], 3)
>>> lpr.set_upper([4,1,2,0], 3)
>>> lpr.is_avoiding_sure_loss()
True
>>> lpr.is_coherent()
True
>>> lpr.is_linear()
False
>>> print(lpr.get_lower([1,0,0,0]))
0.5
>>> print(lpr.get_upper([1,0,0,0]))
0.75
>>> list(lpr)
[((4.0, 2.0, 1.0, 0.0), 3.0, False), ((-4.0, -1.0, -2.0, 0.0), -3.0, False)]
>>> list(decision.filter_maximal([[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]], lpr.dominates))
[[1, 0, 0, 0], [0, 1, 0, 0]]
>>> list(decision.filter_maximal([[0,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]], lpr.dominates))
[[0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
 
