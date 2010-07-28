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

Any iterable of distinct immutable objects can be used to represent a
possibility space. For instance, a ``tuple`` can always be used to
represent a possibility space. [#pspacetuple]_ Any possibility space
can be converted to its ``tuple`` representation via:

.. autofunction:: make_pspace

For more advanced usage of possibility spaces, use the following class:

.. autoclass:: PSpace
   :members:

   .. automethod:: __repr__

   .. automethod:: __str__

.. _gambles:

Gambles
-------

For a possibility space *pspace*, any Python object *mapping* for which::

    (float(mapping[omega]) for omega in pspace)

can be iterated over, represents a gamble. For instance, a ``dict``
can always be used to represent a gamble. If your *pspace* is a simple
range of consequetive integers starting from zero, then you can also
use a ``list`` or ``tuple`` for gamble.

Any gamble can be converted to its ``dict`` representation via:

.. autofunction:: make_gamble

For more advanced usage of gambles, use the following class:

.. autoclass:: Gamble
   :members:

   .. automethod:: __repr__

   .. automethod:: __str__

.. _events:

Events
------

For a possibility space *pspace*, any Python object *elements* for which::

    (omega in elements for omega in pspace)

can be iterated over, represents an event. For instance, a ``set`` can
always be used to represent an event.

Any event can be converted to its ``set`` representation via:

.. autofunction:: make_event

For more advanced usage of events, use the following class:

.. autoclass:: Event
   :members:

   .. automethod:: __repr__

   .. automethod:: __str__

Set Functions
-------------

.. autoclass:: SetFunction
   :members:

.. rubric:: Footnotes

.. [#pspacetuple]

   We use ``tuple`` rather than ``set`` because usually possibility
   spaces have a natural ordering, and ``tuple`` is closest to an
   ordered set.
