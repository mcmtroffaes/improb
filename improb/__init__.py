# improb is a Python module for working with imprecise probabilities
# Copyright (c) 2008-2010, Matthias Troffaes
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""improb is a Python module for working with imprecise probabilities."""

from __future__ import division, absolute_import, print_function

__version__ = '0.1.0'

from abc import ABCMeta, abstractmethod, abstractproperty
from cdd import NumberTypeable
import collections
import fractions
import itertools

class PSpace(collections.Set, collections.Hashable):
    """An immutable possibility space, derived from
    :class:`collections.Set` and :class:`collections.Hashable`. This
    is effectively an immutable ordered set with a fancy constructor.
    """

    def __init__(self, *args):
        """Convert *args* into a possibility space.

        :param args: The components of the space.
        :type args: :class:`collections.Iterable` or :class:`int`

        Some examples of how components can be specified:

        * A range of integers.

          .. doctest::

             >>> list(PSpace(xrange(2, 15, 3)))
             [2, 5, 8, 11, 14]

        * A string.

          .. doctest::

             >>> list(PSpace('abcdefg'))
             ['a', 'b', 'c', 'd', 'e', 'f', 'g']

        * A list of strings.

          .. doctest::

             >>> list(PSpace('rain cloudy sunny'.split(' ')))
             ['rain', 'cloudy', 'sunny']

        * As a special case, you can also specify just a single integer. This
          will be converted to a tuple of integers of the corresponding length.

          .. doctest::

             >>> list(PSpace(3))
             [0, 1, 2]

        If multiple arguments are specified, the product is calculated:

        .. doctest::

           >>> list(PSpace(3, 'abc')) # doctest: +NORMALIZE_WHITESPACE
           [(0, 'a'), (0, 'b'), (0, 'c'),
            (1, 'a'), (1, 'b'), (1, 'c'),
            (2, 'a'), (2, 'b'), (2, 'c')]
           >>> list(PSpace(('rain', 'cloudy', 'sunny'), ('cold', 'warm'))) # doctest: +NORMALIZE_WHITESPACE
           [('rain', 'cold'), ('rain', 'warm'),
            ('cloudy', 'cold'), ('cloudy', 'warm'),
            ('sunny', 'cold'), ('sunny', 'warm')]

        Duplicates are automatically removed:

        .. doctest::

           >>> list(PSpace([2, 2, 5, 3, 9, 5, 1, 2]))
           [2, 5, 3, 9, 1]
        """
        if not args:
            raise ValueError('specify at least one argument')
        elif len(args) == 1:
            arg = args[0]
            if isinstance(arg, int):
                self._data = tuple(xrange(arg))
            elif isinstance(arg, collections.Iterable):
                # rationale for removing duplicates: if elem is not in
                # added, then added.add(elem) is executed and the
                # expression returns True (since set.add() is always
                # False); however, if elem is in added, then the
                # expression returns False (and added.add(elem) is not
                # executed)
                added = set()
                self._data = tuple(
                    elem for elem in arg
                    if elem not in added and not added.add(elem))
            else:
                raise TypeError(
                    'specify possibility space as iterable or integer')
        else:
            self._data = tuple(
                itertools.product(*[PSpace(arg) for arg in args]))

    @classmethod
    def make(cls, pspace):
        """If *pspace* is a :class:`~improb.PSpace`, then returns *pspace*.
        Otherwise, converts *pspace* to a :class:`~improb.PSpace`.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :return: A possibility space.
        :rtype: :class:`~improb.PSpace`
        """
        return pspace if isinstance(pspace, cls) else cls(pspace)

    def make_event(self, event):
        """If *event* is a :class:`Event`, then checks possibility
        space and returns *event*. Otherwise, converts *event* to a
        :class:`Event`.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param event: The event.
        :type event: |eventtype|
        :return: A event.
        :rtype: :class:`Event`
        :raises: :exc:`~exceptions.ValueError` if possibility spaces do not match
        """
        if isinstance(event, Event):
            if self != event.pspace:
                raise ValueError('possibility space mismatch')
            return event
        elif event is True:
            return Event(self, event)
        elif event is False:
            return Event(self, event)
        elif isinstance(event, Gamble):
            if self != event.pspace:
                raise ValueError('possibility space mismatch')
            if not(set(event.itervalues()) <= set([0, 1])):
                raise ValueError("not an indicator gamble")
            return Event(self, (omega for omega, value in event.iteritems()
                                if value == 1))
        else:
            return Event(self, event)

    def __len__(self):
        return len(self._data)

    def __contains__(self, omega):
        return omega in self._data

    def __getitem__(self, index):
        return self._data[index]

    def __iter__(self):
        return iter(self._data)

    def __hash__(self):
        return hash(self._data)

    def __repr__(self):
        """
        >>> PSpace([2, 4, 5])
        PSpace([2, 4, 5])
        >>> PSpace([0, 1, 2])
        PSpace(3)
        """
        if list(self) == list(xrange(len(self))):
            return "PSpace(%i)" % len(self)
        else:
            return "PSpace(%s)" % repr(list(self))

    def __str__(self):
        """
        >>> print(PSpace([2, 4, 5]))
        2 4 5
        """
        return " ".join(str(omega) for omega in self)

    def subsets(self, event=True):
        r"""Iterates over all subsets of the possibility space.

        :param event: An event (optional).
        :type event: |eventtype|
        :returns: Yields all subsets.
        :rtype: Iterator of :class:`Event`.

        >>> pspace = PSpace([2, 4, 5])
        >>> print("\n---\n".join(str(subset) for subset in pspace.subsets()))
        2 : 0
        4 : 0
        5 : 0
        ---
        2 : 1
        4 : 0
        5 : 0
        ---
        2 : 0
        4 : 1
        5 : 0
        ---
        2 : 0
        4 : 0
        5 : 1
        ---
        2 : 1
        4 : 1
        5 : 0
        ---
        2 : 1
        4 : 0
        5 : 1
        ---
        2 : 0
        4 : 1
        5 : 1
        ---
        2 : 1
        4 : 1
        5 : 1
        >>> print("\n---\n".join(str(subset) for subset in pspace.subsets([2, 4])))
        2 : 0
        4 : 0
        5 : 0
        ---
        2 : 1
        4 : 0
        5 : 0
        ---
        2 : 0
        4 : 1
        5 : 0
        ---
        2 : 1
        4 : 1
        5 : 0
        """
        event = self.make_event(event)
        for subset_size in xrange(len(event) + 1):
            for subset in itertools.combinations(event, subset_size):
                yield Event(self, subset)

class Gamble(collections.Mapping, collections.Hashable, NumberTypeable):
    """An immutable gamble.

    >>> pspace = PSpace('abc')
    >>> f1 = Gamble(pspace, {'a': 1, 'b': 4, 'c': 8}, 'fraction')
    >>> print(f1)
    a : 1
    b : 4
    c : 8
    >>> print(f1 + 2)
    a : 3
    b : 6
    c : 10
    >>> print(f1 - 2)
    a : -1
    b : 2
    c : 6
    >>> print(f1 * 2)
    a : 2
    b : 8
    c : 16
    >>> print(f1 / 3)
    a : 1/3
    b : 4/3
    c : 8/3
    >>> f2 = Gamble(pspace, {'a': 5, 'b': 8, 'c': 7}, 'fraction')
    >>> print(f1 + f2)
    a : 6
    b : 12
    c : 15
    >>> print(f1 - f2)
    a : -4
    b : -4
    c : 1
    >>> print(f1 * f2) # doctest: +ELLIPSIS
    a : 5
    b : 32
    c : 56
    >>> print(f1 / f2) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: ...
    >>> event = Event(pspace, 'ac')
    >>> print(f1 + event)
    a : 2
    b : 4
    c : 9
    >>> print(f1 - event)
    a : 0
    b : 4
    c : 7
    >>> print(f1 * event)
    a : 1
    b : 0
    c : 8
    >>> print(f1 / event)
    Traceback (most recent call last):
        ...
    TypeError: ...
    """
    def __init__(self, pspace, data, number_type='float'):
        """Construct a gamble on the given possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param data: The specification of a gamble.
        :type data: |gambletype|
        :param number_type: The type to use for numbers: ``'float'`` or ``'fraction'``.
        :type number_type: ``type``
        """
        NumberTypeable.__init__(self, number_type)
        self._pspace = PSpace.make(pspace)
        if isinstance(data, collections.Mapping):
            self._data = dict((omega, self.make_number(data.get(omega, 0)))
                              for omega in self.pspace)
        elif isinstance(data, collections.Sequence):
            if len(data) < len(self.pspace):
                raise ValueError("data sequence too short")
            self._data = dict((omega, self.make_number(value))
                              for omega, value
                              in itertools.izip(self.pspace, data))
        else:
            raise TypeError('specify data as sequence or mapping')

    @property
    def pspace(self):
        """A :class:`~improb.PSpace` representing the possibility space."""
        return self._pspace

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        # preserve ordering of pspace! so not iter(self._data) but...
        return iter(self._pspace)

    def __contains__(self, omega):
        return omega in self._data

    def __getitem__(self, omega):
        return self._data[omega]

    def __hash__(self):
        return hash((self._pspace,
                     tuple(self._data[omega] for omega in self._pspace)))

    def __repr__(self):
        """
        >>> Gamble([2, 3, 4], {2: 1, 3: 4, 4: 8}, 'float') # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace([2, 3, 4]),
               mapping={2: 1.0,
                        3: 4.0,
                        4: 8.0})
        >>> Gamble([2, 3, 4], {2: '2/6', 3: '4.0', 4: 8}, 'fraction') # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace([2, 3, 4]),
               mapping={2: '1/3',
                        3: 4,
                        4: 8})
        """
        return "Gamble(pspace={0}, mapping={{{1}}})".format(
            # custom formatting of self._data in order to preserve ordering
            # of pspace
            repr(self._pspace),
            ", ".join("{0}: {1}".format(repr(omega), self.number_repr(value))
                      for omega, value in self.iteritems()))

    def __str__(self):
        """
        >>> pspace = PSpace('rain sun clouds'.split())
        >>> print(Gamble(pspace, {'rain': -14, 'sun': 4, 'clouds': 20}))
        rain   : -14.0
        sun    : 4.0
        clouds : 20.0
        """
        maxlen_pspace = max(len(str(omega)) for omega in self.pspace)
        return "\n".join(
            "{0: <{1}} : {2}".format(
                omega, maxlen_pspace, self.number_str(value))
            for omega, value in self.iteritems())

    def _scalar(self, other, oper):
        """
        :raises: :exc:`~exceptions.TypeError` if other is not a scalar
        """
        other = self.make_number(other)
        return Gamble(self.pspace,
                      [oper(value, other) for value in self.itervalues()],
                      self.number_type)

    def _pointwise(self, other, oper):
        """
        :raises: :exc:`~exceptions.ValueError` if possibility spaces do not match
        """
        if isinstance(other, Gamble):
            if self.pspace != other.pspace:
                raise ValueError("possibility space mismatch")
            if self.number_type != other.number_type:
                raise ValueError("number type mismatch")
            return Gamble(
                self.pspace,
                [oper(value, other_value)
                 for value, other_value
                 in itertools.izip(self.itervalues(), other.itervalues())],
                self.number_type)
        elif isinstance(other, Event):
            return self._pointwise(
                other.indicator(self.number_type), oper)
        else:
            # will raise a type error if operand is not scalar
            return self._scalar(other, oper)

    __add__ = lambda self, other: self._pointwise(other, self.NumberType.__add__)
    __sub__ = lambda self, other: self._pointwise(other, self.NumberType.__sub__)
    __mul__ = lambda self, other: self._pointwise(other, self.NumberType.__mul__)
    __truediv__ = lambda self, other: self._scalar(other, self.NumberType.__truediv__)

    def __neg__(self):
        return Gamble(self.pspace, [-value for value in self.itervalues()],
                      self.number_type)

class Event(collections.Set, collections.Hashable):
    """An immutable event.

    >>> pspace = PSpace('abcdef')
    >>> event1 = Event(pspace, 'acd')
    >>> print(event1)
    a : 1
    b : 0
    c : 1
    d : 1
    e : 0
    f : 0
    >>> event2 = Event(pspace, 'cdef')
    >>> print(event2)
    a : 0
    b : 0
    c : 1
    d : 1
    e : 1
    f : 1
    >>> print(event1 & event2)
    a : 0
    b : 0
    c : 1
    d : 1
    e : 0
    f : 0
    >>> print(event1 | event2)
    a : 1
    b : 0
    c : 1
    d : 1
    e : 1
    f : 1
    """
    def __init__(self, pspace, data=False):
        """Construct an event on the given possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param data: The specification of an event.
        :type data: |eventtype|
        """
        self._pspace = PSpace.make(pspace)
        if isinstance(data, collections.Iterable):
            self._data = frozenset(omega for omega in data
                                   if omega in self.pspace)
        elif data is True:
            self._data = frozenset(self.pspace)
        elif data is False:
            self._data = frozenset()
        else:
            raise TypeError("specify data as iterable, True, or False")

    @property
    def pspace(self):
        """An :class:`~improb.PSpace` representing the possibility space."""
        return self._pspace

    # must override this because the class constructor does not accept
    # an iterable for an input
    def _from_iterable(self, it):
        return Event(self._pspace, it)

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return (omega for omega in self._pspace if omega in self._data)

    def __contains__(self, omega):
        return omega in self._data

    def __hash__(self):
        return hash((self._pspace, self._data))

    def __repr__(self):
        """
        >>> pspace = PSpace([2, 3, 4])
        >>> Event(pspace, [3, 4])
        Event(pspace=PSpace([2, 3, 4]), elements=set([3, 4]))
        """
        return "Event(pspace=%s, elements=%s)" % (repr(self.pspace), repr(set(self)))

    def __str__(self):
        """
        >>> pspace = PSpace('rain sun clouds'.split())
        >>> print(Event(pspace, 'rain clouds'.split()))
        rain   : 1
        sun    : 0
        clouds : 1
        """
        maxlen_pspace = max(len(str(omega)) for omega in self.pspace)
        return "\n".join(
            "{0: <{1}} : {2}".format(
                omega, maxlen_pspace, 1 if omega in self else 0)
            for omega in self.pspace)

    def indicator(self, number_type='float'):
        """Return indicator gamble for the event.

        :param number_type: The number type.
        :type number_type: :class:`str`
        :return: Indicator gamble.
        :rtype: :class:`Gamble`

        >>> pspace = PSpace(5)
        >>> event = Event(pspace, [2, 4])
        >>> event.indicator('fraction') # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace(5),
               mapping={0: 0,
                        1: 0,
                        2: 1,
                        3: 0,
                        4: 1})
        >>> event.indicator('float') # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace(5),
               mapping={0: 0.0,
                        1: 0.0,
                        2: 1.0,
                        3: 0.0,
                        4: 1.0})
        """
        return Gamble(self.pspace,
                      dict((omega, 1 if omega in self else 0)
                           for omega in self.pspace),
                      number_type)

    def is_true(self):
        return len(self) == len(self.pspace)

    def is_false(self):
        return len(self) == 0

    def is_singleton(self):
        return len(self) == 1
