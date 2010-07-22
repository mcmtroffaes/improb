Introduction
============

.. currentmodule:: improb

.. testsetup::

   import improb
   import itertools

In brief, use ``tuple`` for possibility spaces, ``dict`` for gambles,
and ``set`` for events. In more detail:

.. _possibility-spaces:

Possibility Spaces
------------------

.. autofunction:: make_pspace

When constructing a possibility space, you can use any iterable of
distinct immutable objects. For example:

* A range of integers.

  .. doctest::

     >>> improb.make_pspace(xrange(2, 15, 3))
     (2, 5, 8, 11, 14)

* A string.

  .. doctest::

     >>> improb.make_pspace('abcdefg')
     ('a', 'b', 'c', 'd', 'e', 'f', 'g')

* A list of strings.

  .. doctest::

     >>> improb.make_pspace('rain cloudy sunny'.split(' '))
     ('rain', 'cloudy', 'sunny')

* A product of possibility spaces.

  .. doctest::

     >>> improb.make_pspace(itertools.product(('rain', 'cloudy', 'sunny'), ('cold', 'warm')))
     (('rain', 'cold'), ('rain', 'warm'), ('cloudy', 'cold'), ('cloudy', 'warm'), ('sunny', 'cold'), ('sunny', 'warm'))  

* As a special case, you can also specify just a single integer. This
  will be converted to a tuple of integers of the corresponding length.

  .. doctest::

     >>> improb.make_pspace(3)
     (0, 1, 2)

* Finally, if no arguments are specified, then the default space is
  just one with two elements.

  .. doctest::

     >>> improb.make_pspace()
     (0, 1)

.. _gambles:

Gambles
-------

.. autofunction:: make_gamble

For a possibility space *pspace*, any Python object *mapping* for which::

    (float(mapping[omega]) for omega in pspace)

can be iterated over, represents a gamble. For instance, a ``dict``
can always be used to represent a gamble. If your *pspace* is a simple
range of consequetive integers starting from zero, then you can also
use a ``list`` or ``tuple`` for gamble.

Any gamble can be converted to its ``dict`` representation via
:func:`make_gamble`.

.. doctest::

   >>> pspace = improb.make_pspace(5)
   >>> improb.make_gamble(pspace, [1, 9, 2, 3, 6])
   {0: 1.0, 1: 9.0, 2: 2.0, 3: 3.0, 4: 6.0}

.. _events:

Events
------

.. autofunction:: make_event

For a possibility space *pspace*, any Python object *elements* for which::

    (omega in elements for omega in pspace)

can be iterated over, represents an event. For instance, a ``set`` can
always be used to represent an event.

Any event can be converted to its ``set`` representation via
:func:`make_event`.

.. doctest::

   >>> pspace = improb.make_pspace(6)
   >>> improb.make_event(pspace, xrange(1, 4))
   set([1, 2, 3])
