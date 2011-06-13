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

.. _possibility-spaces:

Possibility Spaces
------------------

Any :class:`collections.Iterable` of immutable objects can be used to
specify a possibility space. Effectively, an
:class:`collections.Iterable` *pspace* is interpreted as an ordered
:class:`set`.

For convenience, you can also construct a possibility space from any
integer ``n``---this is equivalent to specifying ``range(n)``.

For further convenience, you can construct Cartesian products simply
by specifying multiple iterables or integers.

.. autoclass:: PSpace
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
