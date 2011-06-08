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
   .. automethod:: __add__
   .. automethod:: __sub__

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

Solving the decision tree for the oil wildcatter example in
[#kikuti2005]_:

>>> # specify the decision tree
>>> pspace = PSpace('SWD', 'NOC') # soak, wet, dry; no, open, closed
>>> S = pspace.make_event('S', 'NOC', name="soak")
>>> W = pspace.make_event('W', 'NOC', name="wet")
>>> D = pspace.make_event('D', 'NOC', name="dry")
>>> N = pspace.make_event('SWD', 'N', name="no")
>>> O = pspace.make_event('SWD', 'O', name="open")
>>> C = pspace.make_event('SWD', 'C', name="closed")
>>> lpr = LowPoly(pspace)
>>> t0 = 0
>>> t1 = Chance(pspace)
>>> t1[S] = 20
>>> t1[W] = 5
>>> t1[D] = -7
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
>>> lpr = LowPoly(pspace)
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

Solving the lake district example:

>>> c = 1 # cost of newspaper
>>> pspace = PSpace('rs','RS')
>>> R_ = pspace.make_event('r', 'RS', name='predict rain')
>>> S_ = pspace.make_event('s', 'RS', name='predict sunshine')
>>> R = pspace.make_event('rs', 'R', name='rain')
>>> S = pspace.make_event('rs', 'S', name='sunshine')
>>> t0 = Chance(pspace)
>>> t0[R] = 10
>>> t0[S] = 15
>>> t1 = Chance(pspace)
>>> t1[R] = 5
>>> t1[S] = 20
>>> t = Decision()
>>> t["take waterproof"] = t0
>>> t["no waterproof"] = t1
>>> s = Chance(pspace)
>>> s[R_] = t
>>> s[S_] = t
>>> u = Decision()
>>> u["buy newspaper"] = s - c
>>> u["do not buy"] = t
>>> print(u)
#--buy newspaper--O--predict rain------#--take waterproof--O--rain------:9.0
   |                 |                    |                   |
   |                 |                    |                   sunshine--:14.0
   |                 |                    |
   |                 |                    no waterproof----O--rain------:4.0
   |                 |                                        |
   |                 |                                        sunshine--:19.0
   |                 |
   |                 predict sunshine--#--take waterproof--O--rain------:9.0
   |                                      |                   |
   |                                      |                   sunshine--:14.0
   |                                      |
   |                                      no waterproof----O--rain------:4.0
   |                                                          |
   |                                                          sunshine--:19.0
   |
   do not buy-----#--take waterproof--O--rain------:10.0
		     |                   |
		     |                   sunshine--:15.0
		     |
		     no waterproof----O--rain------:5.0
					 |
					 sunshine--:20.0
>>> lpr = LowPoly(pspace)
>>> lpr[R_ & R, True] = (0.42 * 0.9, None)
>>> lpr[R_ & S, True] = (0.18 * 0.9, None)
>>> lpr[S_ & R, True] = (0.08 * 0.9, None)
>>> lpr[S_ & S, True] = (0.32 * 0.9, None)
>>> for c in [0.579, 0.581, 1.579, 1.581]:
...     print("newspaper cost = {0}".format(c))
...     u["buy newspaper"] = s - c
...     opt = OptLowPrevMax(lpr)
...     for gamble, normal_tree in u.get_norm_back_opt(opt):
...         print(normal_tree)
newspaper cost = 0.579
#--buy newspaper--O--predict rain------#--take waterproof--O--rain------:9.421
		     |                                        |
		     |                                        sunshine--:14.421
		     |
		     predict sunshine--#--no waterproof--O--rain------:4.421
							    |
							    sunshine--:19.421
newspaper cost = 0.581
#--buy newspaper--O--predict rain------#--take waterproof--O--rain------:9.419
		     |                                        |
		     |                                        sunshine--:14.419
		     |
		     predict sunshine--#--no waterproof--O--rain------:4.419
							    |
							    sunshine--:19.419
#--do not buy--#--take waterproof--O--rain------:10.0
				      |
				      sunshine--:15.0
#--do not buy--#--no waterproof--O--rain------:5.0
				    |
				    sunshine--:20.0
newspaper cost = 1.579
#--buy newspaper--O--predict rain------#--take waterproof--O--rain------:8.421
		     |                                        |
		     |                                        sunshine--:13.421
		     |
		     predict sunshine--#--no waterproof--O--rain------:3.421
							    |
							    sunshine--:18.421
#--do not buy--#--take waterproof--O--rain------:10.0
				      |
				      sunshine--:15.0
#--do not buy--#--no waterproof--O--rain------:5.0
				    |
				    sunshine--:20.0
newspaper cost = 1.581
#--do not buy--#--take waterproof--O--rain------:10.0
				      |
				      sunshine--:15.0
#--do not buy--#--no waterproof--O--rain------:5.0
				    |
				    sunshine--:20.0

.. rubric:: Footnotes

.. [#kikuti2005]

    Kikuti, D., Cozman, F., de Campos, C.: Partially ordered preferences
    in decision trees: Computing strategies with imprecision in
    probabilities. In: R. Brafman, U. Junker (eds.) IJCAI-05
    Multidisciplinary Workshop on Advances in Preference Handling,
    pp. 118–123, 2005.
