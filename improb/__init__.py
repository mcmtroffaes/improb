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
import collections
from fractions import Fraction
import itertools

def _fraction(value):
    """Convert value to a :class:`~fractions.Fraction`."""
    # python 2.6 doesn't define Fraction(float)
    # this is a quick hack around that
    if isinstance(value, float):
        return Fraction.from_float(value)
    else:
        return Fraction(value)

def _fraction_repr(value):
    if value.denominator == 1:
        return repr(value.numerator)
    else:
        floatstr = str(float(value))
        if value == Fraction(floatstr):
            return repr(floatstr)
        else:
            return repr(str(value))

def make_pspace(*args):
    """Convert *args* into a possibility space.

    :param args: The components of the space.
    :type args: :class:`collections.Iterable` or :class:`int`
    :returns: A possibility space.
    :rtype: :class:`tuple`

    Some examples of how components can be specified:

    * A range of integers.

      .. doctest::

         >>> make_pspace(xrange(2, 15, 3))
         (2, 5, 8, 11, 14)

    * A string.

      .. doctest::

         >>> make_pspace('abcdefg')
         ('a', 'b', 'c', 'd', 'e', 'f', 'g')

    * A list of strings.

      .. doctest::

         >>> make_pspace('rain cloudy sunny'.split(' '))
         ('rain', 'cloudy', 'sunny')

    * As a special case, you can also specify just a single integer. This
      will be converted to a tuple of integers of the corresponding length.

      .. doctest::

         >>> make_pspace(3)
         (0, 1, 2)

    * Finally, if no arguments are specified, then the default space is
      just one with two elements.

      .. doctest::

         >>> make_pspace()
         (0, 1)

    If multiple arguments are specified, the product is calculated:

    .. doctest::

       >>> make_pspace(3, 'abc') # doctest: +NORMALIZE_WHITESPACE
       ((0, 'a'), (0, 'b'), (0, 'c'),
        (1, 'a'), (1, 'b'), (1, 'c'),
        (2, 'a'), (2, 'b'), (2, 'c'))
       >>> make_pspace(('rain', 'cloudy', 'sunny'), ('cold', 'warm')) # doctest: +NORMALIZE_WHITESPACE
       (('rain', 'cold'), ('rain', 'warm'),
        ('cloudy', 'cold'), ('cloudy', 'warm'),
        ('sunny', 'cold'), ('sunny', 'warm'))

    It also removes duplicates:

    .. doctest::

       >>> make_pspace([2, 2, 5, 3, 9, 5, 1, 2])
       (2, 5, 3, 9, 1)
    """
    if not args:
        return (0, 1)
    elif len(args) == 1:
        arg = args[0]
        if isinstance(arg, int):
            return tuple(xrange(arg))
        else:
            # rationale for removing duplicates: if elem is not in
            # added, then added.add(elem) is executed and the
            # expression returns True (since set.add() is always
            # False); however, if elem is in added, then the
            # expression returns False (and added.add(elem) is not
            # executed)
            added = set()
            return tuple(elem for elem in arg
                         if elem not in added and not added.add(elem))
    else:
        return tuple(itertools.product(*[make_pspace(arg) for arg in args]))

def make_gamble(pspace, mapping):
    """Convert *mapping* into a gamble on *pspace*.

    :returns: A gamble.
    :rtype: :class:`dict`

    >>> pspace = make_pspace(5)
    >>> make_gamble(pspace, [1, 9, 2, 3, 6]) # doctest: +NORMALIZE_WHITESPACE
    {0: Fraction(1, 1),
     1: Fraction(9, 1),
     2: Fraction(2, 1),
     3: Fraction(3, 1),
     4: Fraction(6, 1)}
    """
    return dict((omega, _fraction(mapping[omega])) for omega in pspace)

def make_event(pspace, elements):
    """Convert *elements* into an event on *pspace*.

    :returns: An event.
    :rtype: :class:`set`

    >>> pspace = make_pspace(6)
    >>> make_event(pspace, xrange(1, 4))
    set([1, 2, 3])
    """
    return set(omega for omega in pspace if omega in elements)

class PSpace(collections.Set, collections.Sequence, collections.Hashable):
    """An immutable possibility space with syntactic sugar, derived
    from :class:`collections.Set`, :class:`collections.Sequence`, and
    :class:`collections.Hashable`.
    """

    def __init__(self, *args):
        self._data = make_pspace(*args)

    @staticmethod
    def make(pspace):
        """If *pspace* is a :class:`~improb.PSpace`, then returns *pspace*.
        Otherwise, converts *pspace* to a :class:`~improb.PSpace`.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :return: A possibility space.
        :rtype: :class:`~improb.PSpace`
        """
        return pspace if isinstance(pspace, PSpace) else PSpace(pspace)

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

    def make_element(self, obj):
        """Convert the given indicator gamble, or event, into an
        element of self.

        >>> pspace = PSpace(3)
        >>> pspace.make_element(1)
        1
        >>> pspace.make_element(Event(pspace, [2]))
        2
        >>> pspace.make_element(Gamble(pspace, [1, 0, 0]))
        0
        >>> pspace = PSpace('abc')
        >>> pspace.make_element('c')
        'c'
        >>> pspace.make_element(Event(pspace, ['a']))
        'a'
        >>> pspace.make_element(Gamble(pspace, {'a': 0, 'b': 1, 'c': 0}))
        'b'
        >>> pspace = PSpace(3)
        >>> pspace.make_element(Event(pspace, [1, 2])) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: not a singleton
        >>> pspace.make_element(Gamble(pspace, [1, 1, 0])) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: not a singleton
        >>> pspace.make_element(Gamble(pspace, [1, 2, 0]))
        Traceback (most recent call last):
            ...
        ValueError: not an indicator gamble
        """
        if obj in self:
            return obj
        event = Event.make(self, obj)
        if len(event) != 1:
            raise ValueError('not a singleton')
        return list(event)[0]

    def subsets(self, event=None):
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
        if event is None:
            event = self
        elif not isinstance(event, set):
            event = make_event(self, event)
        for subset_size in xrange(len(event) + 1):
            for subset in itertools.combinations(event, subset_size):
                yield Event(self, subset)

class Gamble(collections.Mapping, collections.Hashable):
    """An immutable gamble.

    >>> pspace = PSpace('abc')
    >>> f1 = Gamble(pspace, {'a': 1, 'b': 4, 'c': 8})
    >>> print(f1 + 2)
    a :  3.000
    b :  6.000
    c : 10.000
    >>> print(f1 - 2)
    a : -1.000
    b :  2.000
    c :  6.000
    >>> print(f1 * 2)
    a :  2.000
    b :  8.000
    c : 16.000
    >>> print(f1 / 2)
    a : 0.500
    b : 2.000
    c : 4.000
    >>> f2 = Gamble(pspace, {'a': 5, 'b': 8, 'c': 7})
    >>> print(f1 + f2)
    a :  6.000
    b : 12.000
    c : 15.000
    >>> print(f1 - f2)
    a : -4.000
    b : -4.000
    c :  1.000
    >>> print(f1 * f2) # doctest: +ELLIPSIS
    a :  5.000
    b : 32.000
    c : 56.000
    >>> print(f1 / f2) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: ...
    >>> event = Event(pspace, 'ac')
    >>> print(f1 + event)
    a : 2.000
    b : 4.000
    c : 9.000
    >>> print(f1 - event)
    a : 0.000
    b : 4.000
    c : 7.000
    >>> print(f1 * event)
    a : 1.000
    b : 0.000
    c : 8.000
    >>> print(f1 / event)
    Traceback (most recent call last):
        ...
    TypeError: ...
    """
    def __init__(self, pspace, mapping):
        """Construct a gamble on the given possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param mapping: A mapping that defines the values of the gamble.
        :type mapping: |gambletype|
        """
        self._pspace = PSpace.make(pspace)
        self._data = make_gamble(pspace, mapping)

    @staticmethod
    def make(pspace, gamble):
        """If *gamble* is a :class:`Gamble`, then checks possibility
        space and returns *gamble*. Otherwise, converts *gamble* to a
        :class:`Gamble`.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param gamble: The gamble.
        :type gamble: |gambletype|
        :return: A gamble.
        :rtype: :class:`Gamble`
        :raises: :exc:`~exceptions.ValueError` if possibility spaces do not match

        >>> pspace = PSpace('abc')
        >>> event = Event.make(pspace, 'ac')
        >>> gamble = event.indicator()
        >>> print(Gamble.make(pspace, 'b'))
        a : 0.000
        b : 1.000
        c : 0.000
        >>> print(Gamble.make(pspace, event))
        a : 1.000
        b : 0.000
        c : 1.000
        >>> print(Gamble.make(pspace, gamble))
        a : 1.000
        b : 0.000
        c : 1.000
        >>> print(Gamble.make(pspace, {'a': 1, 'b': 0, 'c': 8}))
        a : 1.000
        b : 0.000
        c : 8.000
        """
        pspace = PSpace.make(pspace)
        if isinstance(gamble, Gamble):
            if pspace != gamble.pspace:
                raise ValueError('possibility spaces do not match')
            return gamble
        elif isinstance(gamble, Event):
            if pspace != gamble.pspace:
                raise ValueError('possibility spaces do not match')
            return gamble.indicator()
        elif gamble in pspace:
            return Gamble(pspace, dict((omega, 1 if gamble == omega else 0)
                                       for omega in pspace))
        else:
            return Gamble(pspace, gamble)

    @property
    def pspace(self):
        """An :class:`~improb.PSpace` representing the possibility space."""
        return self._pspace

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, omega):
        return omega in self._data

    def __getitem__(self, omega):
        return self._data[omega]

    def __hash__(self):
        return hash((self._pspace,
                     tuple(self._data[omega] for omega in self._pspace)))

    def __repr__(self):
        """
        >>> Gamble([2, 3, 4], {2: 1, 3: 4, 4: 8}) # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace([2, 3, 4]),
               mapping={2: Fraction(1, 1),
                        3: Fraction(4, 1),
                        4: Fraction(8, 1)})
        """
        return "Gamble(pspace={0}, mapping={1})".format(
            repr(self._pspace), repr(self._data))

    def __str__(self):
        """
        >>> pspace = PSpace('rain sun clouds'.split())
        >>> print(Gamble(pspace, {'rain': -14, 'sun': 4, 'clouds': 20}))
        rain   : -14.000
        sun    :   4.000
        clouds :  20.000
        """
        maxlen_pspace = max(len(str(omega)) for omega in self.pspace)
        maxlen_value = max(len("{0:.3f}".format(float(self[omega])))
                           for omega in self.pspace)
        return "\n".join(
            "{0: <{1}} : {2:{3}.3f}".format(
                omega, maxlen_pspace, float(self[omega]), maxlen_value)
            for omega in self.pspace)

    def _scalar(self, other, oper):
        """
        :raises: :exc:`~exceptions.TypeError` if other is not a scalar
        """
        if isinstance(other, (int, long, float, Fraction)):
            return Gamble(self.pspace,
                          dict((omega, oper(self[omega], _fraction(other)))
                               for omega in self.pspace))
        else:
            raise TypeError("argument must be a scalar, not '%s'"
                            % other.__class__)

    def _pointwise(self, other, oper):
        """
        :raises: :exc:`~exceptions.ValueError` if possibility spaces do not match
        """
        if isinstance(other, (int, long, float, Fraction)):
            return self._scalar(other, oper)
        elif isinstance(other, Event):
            if self.pspace != other.pspace:
                raise ValueError("possibility spaces do not match")
            return Gamble(self.pspace,
                          dict((omega, oper(self[omega],
                                            Fraction(1) if omega in other
                                            else Fraction(0)))
                               for omega in self.pspace))
        elif isinstance(other, Gamble):
            if self.pspace != other.pspace:
                raise ValueError("possibility spaces do not match")
            return Gamble(self.pspace,
                          dict((omega, oper(self[omega],
                                            _fraction(other[omega])))
                               for omega in self.pspace))

    __add__ = lambda self, other: self._pointwise(other, Fraction.__add__)
    __sub__ = lambda self, other: self._pointwise(other, Fraction.__sub__)
    __mul__ = lambda self, other: self._pointwise(other, Fraction.__mul__)
    __truediv__ = lambda self, other: self._scalar(other, Fraction.__div__)

    def __neg__(self):
        return Gamble(self.pspace,
                      dict((omega, -self[omega]) for omega in self.pspace))

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
    def __init__(self, pspace, elements):
        self._pspace = PSpace.make(pspace)
        self._data = frozenset(omega for omega in self.pspace
                               if omega in elements)

    @staticmethod
    def make(pspace, event):
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
        pspace = PSpace.make(pspace)
        if isinstance(event, Event):
            if pspace != event.pspace:
                raise ValueError('possibility spaces do not match')
            return event
        elif event is None:
            return Event(pspace, pspace)
        elif isinstance(event, Gamble):
            if set(event.itervalues()) != set([0, 1]):
                raise ValueError("not an indicator gamble")
            return Event(pspace, set(omega for omega, value in event.iteritems()
                                     if value == 1))
        elif event in pspace:
            return Event(pspace, (event,))
        else:
            return Event(pspace, event)

    @property
    def pspace(self):
        """An :class:`~improb.PSpace` representing the possibility space."""
        return self._pspace

    # must override this because the class constructor does not accept
    # an iterable for an input
    def _from_iterable(self, it):
        return Event(self._pspace, set(it))

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

    def indicator(self):
        """Return indicator gamble for the event.

        :return: Indicator gamble.
        :rtype: :class:`Gamble`

        >>> pspace = PSpace(5)
        >>> event = Event(pspace, [2, 4])
        >>> event.indicator() # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace(5),
               mapping={0: Fraction(0, 1),
                        1: Fraction(0, 1),
                        2: Fraction(1, 1),
                        3: Fraction(0, 1),
                        4: Fraction(1, 1)})
        """
        return Gamble(self.pspace, dict((omega, 1 if omega in self else 0)
                                        for omega in self.pspace))

    def is_true(self):
        return len(self) == len(self.pspace)

    def is_false(self):
        return len(self) == 0

    def is_singleton(self):
        return len(self) == 1
