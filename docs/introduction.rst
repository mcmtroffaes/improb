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
*logically independent* whenever collection of events

.. math::

   \{X_1=x_1\}\cup\dots\cup\{X_n=x_n\}

have a non-empty intersection, for all
:math:`x_1\in\mathcal{X}_1,\dots,x_n\in\mathcal{X}_n`. This simply
means that the random vector :math:`(X_1,\dots,X_n)` can take any
value in :math:`\mathcal{X}_1\times\dots\times\mathcal{X}_n`.

In improb, one specifies such collection :math:`\mathbf{X}`
of logically independent
variables simply by deriving each variable :math:`X_1` from :class:`improb.Var`.
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

.. _gambles:

Gambles
-------

Any :class:`collections.Mapping` or :class:`collections.Sequence` can
be used to specify a gamble. Effectively, given a possibility space
*pspace*, a :class:`collections.Mapping` *mapping* corresponds to the
mapping (specified as Python dictionary)::

    {omega: mapping.get(omega, 0) for omega in pspace}

and a :class:`collections.Sequence` *sequence* corresponds to::

    {omega: value for omega, value in zip(pspace, sequence)}

This yields maximum flexibility so you can use the simplest possible
specification for a gamble, depending on the situation.

Internally, the following class is used to represent gambles; it is an
immutable :class:`collections.Mapping`, and supports the usual
pointwise arithmetic operations.

.. autoclass:: Gamble
   :members:

   .. automethod:: __repr__
   .. automethod:: __str__

.. _events:

Events
------

Any :class:`collections.Iterable` can be used to specify an
event. Effectively, given a possibility space *pspace*, an
:class:`collections.Iterable` corresponds to the event (specified as a
Python set)::

    {omega for omega in iterable}

where all elements *omega* must belong to the possibility space
*pspace*.

For convenience, you can also specify an event as :const:`True` (which
corresponds to the full set) or :const:`False` (which corresponds to
the empty set).

Internally, the following class is used to represent events; it is an
immutable :class:`collections.Set`, and supports a few more common
operations.

.. autoclass:: Event
   :members:

   .. automethod:: __repr__
   .. automethod:: __str__
