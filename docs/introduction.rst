Introduction
============

.. module:: improb

.. testsetup::

   import improb
   import itertools

In brief, you can use

* :class:`PSpace` for :ref:`possibility spaces <possibility-spaces>`,
* :class:`tuple`, :class:`list`, :class:`dict`, or :class:`Gamble` for :ref:`gambles <gambles>`, and
* :class:`tuple`, :class:`list`, :class:`set` or :class:`Event` for :ref:`events <events>`.

In more detail:

.. _possibility-spaces:

Possibility Spaces
------------------

Any iterable of distinct immutable objects can be used to represent a
possibility space. For instance, a :class:`tuple` can always be used to
represent a possibility space. [#pspacetuple]_ Any possibility space
can be converted to its :class:`tuple` representation via:

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

can be iterated over, represents a gamble. For instance, a :class:`dict`
can always be used to represent a gamble. If your *pspace* is a simple
range of consequetive integers starting from zero, then you can also
use a ``list`` or :class:`tuple` for gamble.

Any gamble can be converted to its :class:`dict` representation via:

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

can be iterated over, represents an event. For instance, a :class:`set` can
always be used to represent an event.

Any event can be converted to its :class:`set` representation via:

.. autofunction:: make_event

For more advanced usage of events, use the following class:

.. autoclass:: Event
   :members:

   .. automethod:: __repr__
   .. automethod:: __str__

.. rubric:: Footnotes

.. [#pspacetuple]

   We use :class:`tuple` rather than :class:`set` because usually possibility
   spaces have a natural ordering, and :class:`tuple` is closest to an
   ordered set.
