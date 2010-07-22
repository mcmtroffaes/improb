Lower Previsions
================

.. currentmodule:: improb.lowprev

.. testsetup::

   from improb.lowprev import LowPrev
   import improb.decision

Methods and Attributes
----------------------

.. autoclass:: LowPrev
   :members:

   .. automethod:: __init__

   .. automethod:: __iter__

Examples
--------

Natural Extension
~~~~~~~~~~~~~~~~~

>>> lpr = LowPrev(4)
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
>>> list(improb.decision.filter_maximal([[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]], lpr.dominates))
[[1, 0, 0, 0], [0, 1, 0, 0]]
>>> list(improb.decision.filter_maximal([[0,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]], lpr.dominates))
[[0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
 
Mobius Inverse
~~~~~~~~~~~~~~

>>> lpr = LowPrev(2)
>>> lpr.set_lower([1,0], 0.3)
>>> lpr.set_lower([0,1], 0.2)
>>> mass = lpr.get_mobius_inverse()
>>> print(mass[frozenset()])
0.0
>>> print(mass[frozenset([0])])
0.3
>>> print(mass[frozenset([1])])
0.2
>>> print(mass[frozenset([0,1])])
0.5

Frechet Bounds
~~~~~~~~~~~~~~

>>> from improb.lowprev import LowPrev
>>> lpr = LowPrev(4)
>>> lpr.set_precise([1,1,0,0], 0.6)
>>> lpr.set_precise([0,1,1,0], 0.7)
>>> lpr.is_avoiding_sure_loss()
True
>>> print "%.6f" % lpr.get_lower([0,1,0,0]) # should be max(0.6+0.7-1,0)
0.300000
>>> print "%.6f" % lpr.get_upper([0,1,0,0]) # should be min(0.6,0.7)
0.600000
