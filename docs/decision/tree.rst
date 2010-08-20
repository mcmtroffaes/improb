.. testsetup::

   from improb import PSpace, Gamble, Event
   from improb.lowprev.lowpoly import LowPoly
   from improb.decision.tree import Tree, Reward, Decision, Chance
   from improb.decision.opt import OptLowPrevMax

.. module:: improb.decision.tree

Decision Trees
==============

.. autoclass:: Tree
   :members:

   .. automethod:: _get_norm_back_opt

.. autoclass:: Reward
   :show-inheritance:
   :members:

.. autoclass:: Decision
   :show-inheritance:
   :members:

.. autoclass:: Chance
   :show-inheritance:
   :members:

Examples
--------

Solving the decision tree for the oil catter example in
[#kikuti2005]_:

>>> # specify the decision tree
>>> pspace = PSpace('SWD', 'NOC') # soak, wet, dry; no, open, closed
>>> S = pspace.make_event('S', 'NOC', name="soak")
>>> W = pspace.make_event('W', 'NOC', name="wet")
>>> D = pspace.make_event('D', 'NOC', name="dry")
>>> N = pspace.make_event('SWD', 'N', name="no")
>>> O = pspace.make_event('SWD', 'O', name="open")
>>> C = pspace.make_event('SWD', 'C', name="closed")
>>> lpr = LowPoly(pspace, number_type='float')
>>> t0 = Reward(0, number_type='float')
>>> t1 = Chance(pspace)
>>> t1[S] = Reward(20, number_type='float')
>>> t1[W] = Reward(5, number_type='float')
>>> t1[D] = Reward(-7, number_type='float')
>>> t = Decision()
>>> t["not drill"] = t0
>>> t["drill"] = t1
>>> ss = t - 1
>>> s = Chance(pspace)
>>> s[N] = ss
>>> s[O] = ss
>>> s[C] = ss
>>> u = Decision()
>>> u["sounding"] = s
>>> u["no sounding"] = t
>>> print(u)
#--sounding-----O--no------#--not drill--:-1.0
   |               |          |
   |               |          drill------O--soak--:19.0
   |               |                        |
   |               |                        wet---:4.0
   |               |                        |
   |               |                        dry---:-8.0
   |               |
   |               open----#--not drill--:-1.0
   |               |          |
   |               |          drill------O--soak--:19.0
   |               |                        |
   |               |                        wet---:4.0
   |               |                        |
   |               |                        dry---:-8.0
   |               |
   |               closed--#--not drill--:-1.0
   |                          |
   |                          drill------O--soak--:19.0
   |                                        |
   |                                        wet---:4.0
   |                                        |
   |                                        dry---:-8.0
   |
   no sounding--#--not drill--:0.0
		   |
		   drill------O--soak--:20.0
				 |
				 wet---:5.0
				 |
				 dry---:-7.0
>>> lpr = LowPoly(pspace, number_type='float')
>>> lpr[N, True] = (0.183, 0.222)
>>> lpr[O, True] = (0.333, 0.363)
>>> lpr[C, True] = (0.444, 0.454)
>>> lpr[D, N] = (0.500, 0.666)
>>> lpr[D, O] = (0.222, 0.333)
>>> lpr[D, C] = (0.111, 0.166)
>>> lpr[W, N] = (0.222, 0.272)
>>> lpr[W, O] = (0.363, 0.444)
>>> lpr[W, C] = (0.333, 0.363)
>>> lpr[S, N] = (0.125, 0.181)
>>> lpr[S, O] = (0.250, 0.363)
>>> lpr[S, C] = (0.454, 0.625)
>>> opt = OptLowPrevMax(lpr)
>>> for gamble, normal_tree in u.get_norm_back_opt(opt):
...     print(normal_tree)
#--no sounding--#--drill--O--soak--:20.0
			     |
			     wet---:5.0
			     |
			     dry---:-7.0
>>> # note: backopt should be normopt for maximality!! let's check...
>>> for gamble, normal_tree in u.get_norm_opt(opt):
...     print(normal_tree)
#--no sounding--#--drill--O--soak--:20.0
			     |
			     wet---:5.0
			     |
			     dry---:-7.0

.. rubric:: Footnotes

.. [#kikuti2005]

    Kikuti, D., Cozman, F., de Campos, C.: Partially ordered preferences
    in decision trees: Computing strategies with imprecision in
    probabilities. In: R. Brafman, U. Junker (eds.) IJCAI-05
    Multidisciplinary Workshop on Advances in Preference Handling,
    pp. 118–123, 2005.
