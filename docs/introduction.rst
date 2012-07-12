.. testsetup::

   from improb import *

.. module:: improb

Introduction
============

To get started quickly, use

* :class:`float` or :class:`str` for :ref:`values <values>`,
* :class:`int` or :class:`list` for :ref:`possibility spaces <possibility-spaces>`,
* :class:`list` or :class:`dict` for :ref:`gambles <gambles>`, and
* :class:`list` for :ref:`events <events>`.

The library supports many more modes of operation, to which we turn
next.

.. _values:

Values
------

Throughout the library, you can choose (slow) exact arithmetic with
:class:`fractions.Fraction` (rational numbers), or (fast) approximate
arithmetic with :class:`float` (limited precision reals).

Numbers can be specified directly as instances of
:class:`fractions.Fraction` (e.g. ``fractions.Fraction(1, 3)``) or
:class:`float` (e.g. ``1.23``). You can also use :class:`int`
(e.g. ``20``), or :class:`str` in the form of for instance ``'1.23'``
or ``'1/3'``---these are internally converted to their exact
representation if you work with fractions, or their approximate
representation if you work with floats.

The constructors of lower previsions and gambles have an optional
*number_type* keyword argument: if it is ``'float'`` then float
arithmetic is used, and if it is ``'fraction'`` then rational
arithmetic is used.

If you do not specify a *number_type* on construction, then
``'float'`` is used, unless all values are :class:`fractions.Fraction`
or :class:`str`.

.. seealso::

    :class:`cdd.NumberTypeable`
        A general purpose class for objects which admit different
        numerical representations.

    :func:`cdd.get_number_type_from_value`
        Determine the number type from values.

.. _variables:

Variables
---------

All variables (including gambles and events)
derive from the following base class:

.. autoclass:: ABCVar
   :members:

We say that a collection :math:`\mathbf{X}=\{X_1,\dots,X_n\}`
of (random) variables is
*logically independent* whenever the collection of events

.. math::

   \{X_1=x_1\},\dots,\{X_n=x_n\}

have a non-empty intersection, for all
:math:`x_1\in\mathcal{X}_1,\dots,x_n\in\mathcal{X}_n`. This simply
means that the random vector :math:`(X_1,\dots,X_n)` can take any
value in :math:`\mathcal{X}_1\times\dots\times\mathcal{X}_n`.

In improb, one specifies such collection :math:`\mathbf{X}`
of logically independent
variables simply by deriving each variable :math:`X_i` from :class:`improb.Var`.
These variables are characterized solely by the values they can take.

.. autoclass:: Var
   :members:

   .. automethod:: __init__

Any variables which are *functions* of variables in :math:`\mathbf{X}`
(obviously, these cannot be logically independent from :math:`\mathbf{X}`)
are derived from:

.. autoclass:: Func
   :members:

   .. automethod:: __init__

They represent arbitrary functions of other variables. They
are characterized by a sequence of (not necessarily primitive) input
variables, and their value at any logically possible combination of
values of input variables.

.. _domains:

Domains
-------

A domain is simply a subset of :math:`\mathbf{X}`.  Every variable has
a canonical domain, which consists of a minimal subset of
:math:`\mathbf{X}` for which its values are uniquely determined. One
can think of a domain as a Cartesian product of sets, providing a
possibility space for a random variable.

.. autoclass:: Domain
   :members:

   .. automethod:: __init__
   .. automethod:: __repr__
   .. automethod:: __str__

.. _points:

Points
------

Sets can be refered to in various ways. First, a
:class:`dict` that maps :class:`Var` instances to values::

    a = Var([1, 3, 4])
    b = Var([7, 8, 9])
    c = Var([12, 14, 19])
    dom = Domain(a, c)
    if dom.has_point({a: 3, b: 7, c: 19}):
        print("ok")

is called a *point*. Mathematically,
``{a: 3, b: 7, c: 19}``
is intended to denote the set
:math:`\{A=3\}\cap\{B=7\}\cap\{C=19\}`.

.. autoclass:: Point
   :members:

   .. automethod:: __init__

.. _events:

Events
------

More generally, you can use a :class:`Func`, which maps points to
either ``True`` or ``False``::

    a = Var('abc')
    b = Var([2, 3, 5])
    e = Func([a, b], lambda va, vb: va == 'c' and vb != 3)
    if e.get_value({b: 2, a: 'c'}):
        print("ok")

For improb, any :class:`Func` instance with values in
``{True, False}`` is an event.

.. _gambles:

Gambles
-------

For improb, any :class:`Func` which maps points to real numbers is a
gamble.
