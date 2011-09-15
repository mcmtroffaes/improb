# improb is a Python module for working with imprecise probabilities
# Copyright (c) 2008-2011, Matthias Troffaes
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

# variable implementation is inspired by
# http://openopt.org/FuncDesignerDoc

from __future__ import division, absolute_import, print_function

from abc import ABCMeta, abstractmethod, abstractproperty
import cdd
import collections
import functools
import fractions
import itertools
import numbers
import operator

from improb._compat import OrderedDict, OrderedSet

def _str_keys_values(keys, values):
    """Turn dictionary with *keys* and *values* into a string.
    Warning: *keys* must be a list.
    """
    maxlen_keys = max(len(str(key)) for key in keys)
    return "\n".join(
        "{0: <{1}} : {2}".format(
            key, maxlen_keys, value)
        for key, value in itertools.izip(keys, values))

class Domain(collections.Hashable, collections.Set):
    """An immutable set of :class:`Var`\ s."""

    def __init__(self, *vars_):
        """Construct a domain for the given *vars_*.

        :param vars_: The components of the domain.
        :type vars_: Each component is a :class:`Var`.

        .. doctest::

           >>> a = Var(range(3), name='a')
           >>> Domain(a)
           Domain(Var([0, 1, 2], name='a'))
           >>> Domain(a, a)
           Domain(Var([0, 1, 2], name='a'))
           >>> c = Var(range(3), name='c')
           >>> Domain(a, c)
           Domain(Var([0, 1, 2], name='a'), Var([0, 1, 2], name='c'))
           >>> d = Var(range(3), name='a') # identical to a!
           >>> Domain(a, d)
           Domain(Var([0, 1, 2], name='a'))
           >>> b = Var('abc')
           >>> dom = Domain(a, b)
           >>> list(atom.values() for atom in dom.atoms()) # doctest: +NORMALIZE_WHITESPACE
           [[0, 'a'], [0, 'b'], [0, 'c'],
            [1, 'a'], [1, 'b'], [1, 'c'],
            [2, 'a'], [2, 'b'], [2, 'c']]
           >>> a = Var(['rain', 'cloudy', 'sunny'])
           >>> b = Var(['cold', 'warm'])
           >>> dom = Domain(a, b)
           >>> list(atom.values() for atom in dom.atoms()) # doctest: +NORMALIZE_WHITESPACE
           [['rain', 'cold'], ['rain', 'warm'],
            ['cloudy', 'cold'], ['cloudy', 'warm'],
            ['sunny', 'cold'], ['sunny', 'warm']]
        """
        self._vars = OrderedSet(vars_)
        if any(not isinstance(var, Var) for var in self._vars):
            raise TypeError("expected Var (%s)" % self._vars)

    # must override _from_iterable as __init__ does not accept an iterable
    @classmethod
    def _from_iterable(cls, it):
        return cls(*list(it))

    def __len__(self):
        return len(self._vars)

    def __iter__(self):
        return iter(self._vars)

    def __contains__(self, var):
        return var in self._vars

    def __hash__(self):
        return self._hash()

    def atoms(self):
        """Generate all atoms of the domain."""
        for values in itertools.product(*self._vars):
            yield OrderedDict(itertools.izip(self._vars, values))

    def __repr__(self):
        """
        >>> a = Var([2, 4, 5], name='a')
        >>> b = Var('xy', name='b')
        >>> Domain(a)
        Domain(Var([2, 4, 5], name='a'))
        >>> Domain(a, b)
        Domain(Var([2, 4, 5], name='a'), Var(['x', 'y'], name='b'))
        """
        return (
            "Domain("
            + ", ".join(repr(var) for var in self._vars)
            + ")"
            )

    def __str__(self):
        """
        >>> a = Var([2, 4, 5])
        >>> b = Var('uv')
        >>> print(Domain(a))
        {2, 4, 5}
        >>> print(Domain(a, b))
        {2, 4, 5} x {u, v}
        """
        return (
            " x ".join(
                "{" + ", ".join(str(val) for val in var) + "}"
                for var in self)
            )

    def subsets(self, event=True, empty=True, full=True,
                size=None, contains=False):
        r"""Iterates over all subsets of the possibility space.

        :param event: An event (optional).
        :type event: |eventtype|
        :param empty: Whether to include the empty event or not.
        :type empty: :class:`bool`
        :param full: Whether to include *event* or not.
        :type full: :class:`bool`
        :param size: Any size constraints. If specified, then *empty*
            and *full* are ignored.
        :type size: :class:`int` or :class:`collections.Iterable`
        :param contains: An event that must be contained in all
            returned subsets.
        :type contains: |eventtype|
        :returns: Yields all subsets.
        :rtype: Iterator of :class:`Event`.

        .. todo:: Implement!
        """

        return

        # old tests and code:
        """
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
        >>> print("\n---\n".join(str(subset) for subset in pspace.subsets([2, 4], empty=False, full=False)))
        2 : 1
        4 : 0
        5 : 0
        ---
        2 : 0
        4 : 1
        5 : 0
        >>> print("\n---\n".join(str(subset) for subset in pspace.subsets(True, contains=[4])))
        2 : 0
        4 : 1
        5 : 0
        ---
        2 : 1
        4 : 1
        5 : 0
        ---
        2 : 0
        4 : 1
        5 : 1
        ---
        2 : 1
        4 : 1
        5 : 1
        """
        event = self.make_event(event)
        contains = self.make_event(contains)
        if not(contains <= event):
            # nothing to iterate over!!
            return
        if size is None:
            size_range = xrange(0 if empty else 1,
                                len(event) + (1 if full else 0))
        elif isinstance(size, collections.Iterable):
            size_range = size
        elif isinstance(size, (int, long)):
            size_range = (size,)
        else:
            raise TypeError('invalid size')
        for subset_size in size_range:
            for subset in itertools.combinations(event - contains, subset_size):
                yield Event(self, subset) | contains

class ABCVar(collections.Hashable, collections.Mapping):
    """Abstract base class for variables."""
    __metaclass__ = ABCMeta
    _nextid = 0

    @staticmethod
    def _make_name():
        return "unnamed{0}".format(ABCVar._nextid)
        ABCVar._nextid += 1

    @abstractproperty
    def name(self):
        """Name of the variable.

        :rtype: :class:`str`
        """
        raise NotImplementedError

    @abstractproperty
    def domain(self):
        """Return a domain on which the variable can be evaluated.

        :rtype: :class:`Domain`
        """
        raise NotImplementedError

    @abstractmethod
    def get_value(self, atom, domain):
        """Return value of this variable on *atom*, relative to the
        given *domain*.
        """
        raise NotImplementedError

    def __str__(self):
        return _str_keys_values(
            [atom.values() for atom in self.domain.atoms()],
            [self.get_value(atom, self.domain)
             for atom in self.domain.atoms()]
            )

    def is_equivalent_to(self, other):
        """Check whether two random variables are equivalent."""
        domain = self.domain | other.domain
        for atom in domain.atoms():
            if self.get_value(atom, domain) != other.get_value(atom, domain):
                return False
        return True

class Var(ABCVar):
    """A variable, logically independent of all other :class:`Var`\ s.
    """

    def __init__(self, values, name=None):
        """Construct a variable.

        :param values: The values that the variable can take.
        :type values: Any iterable.

        Some examples of how variables can be specified:

        * A range of integers.

          .. doctest::

             >>> Var(xrange(2, 15, 3), name='a')
             Var([2, 5, 8, 11, 14], name='a')

        * A string.

          .. doctest::

             >>> Var('abcdefg', name='x')
             Var(['a', 'b', 'c', 'd', 'e', 'f', 'g'], name='x')

        * A list of strings.

          .. doctest::

             >>> Var('rain cloudy sunny'.split(' '), name='weather')
             Var(['rain', 'cloudy', 'sunny'], name='weather')

        Duplicates are automatically removed:

        .. doctest::

           >>> Var([2, 2, 5, 3, 9, 5, 1, 2], name='c')
           Var([2, 5, 3, 9, 1], name='c')
        """
        self._name = str(name) if name is not None else self._make_name()
        self._values = OrderedSet(values)
        self._domain = Domain(self)

    def __repr__(self):
        """Return string representation.

        >>> Var(range(3)) # doctest: +ELLIPSIS
        Var([0, 1, 2], name='unnamed...')
        >>> Var(range(3), name='a')
        Var([0, 1, 2], name='a')
        """
        return (
            "Var(["
            + ", ".join(repr(key) for key in self)
            + "], name={0})".format(repr(self.name))
            )

    def __hash__(self):
        return hash((self._name, self._values._hash()))

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def __contains__(self, key):
        return key in self._values

    def __getitem__(self, key):
        if key in self._values:
            return key
        else:
            raise KeyError(str(key))

    @property
    def name(self):
        return self._name

    @property
    def domain(self):
        return self._domain

    def get_value(self, atom, domain):
        """
        >>> a = Var(range(3))
        >>> b = Var(['rain', 'sun'])
        >>> dom = Domain(b, a)
        >>> a.get_value({b: 'sun', a: 2}, dom)
        2
        >>> b.get_value({b: 'sun', a: 2}, dom)
        'sun'
        >>> b.get_value({b: 'blabla', a: 2}, dom) # doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        KeyError: 'blabla'
        """
        # we could simply return atom[self] but that might miss key errors
        return self[atom[self]]

class Func(ABCVar):
    """A function of other variables.

    >>> a = Var(range(2))
    >>> b = Var(['rain', 'sun'])
    >>> c = Func([a, b], {
    ...     (0, 'rain'): -1,
    ...     (0, 'sun'): 2,
    ...     (1, 'rain'): 0,
    ...     (1, 'sun'): 2,
    ...     })
    >>> print(c)
    [0, 'rain'] : -1
    [0, 'sun']  : 2
    [1, 'rain'] : 0
    [1, 'sun']  : 2
    >>> d = Func([c], {(-1,): False, (0,): False, (2,): True})
    >>> print(d)
    [0, 'rain'] : False
    [0, 'sun']  : True
    [1, 'rain'] : False
    [1, 'sun']  : True
    >>> e = Func([b], {('rain',): False, ('sun',): True})
    >>> e.is_equivalent_to(d)
    True
    >>> e.is_equivalent_to(a)
    False
    """

    def __init__(self, inputs, mapping, name=None, validate=True):
        """Construct a function."""
        self._inputs = list(inputs)
        self._mapping = dict(mapping)
        self._domain = functools.reduce(
            operator.or_, (inp.domain for inp in self._inputs))
        if any(not isinstance(inp, ABCVar) for inp in self._inputs):
            raise TypeError("expected sequence of ABCVar for inputs")
        # check that it is well defined
        if validate:
            for atom in self._domain.atoms():
                self.get_value(atom, self._domain)

    def __len__(self):
        return len(self._mapping)

    def __iter__(self):
        return iter(self._mapping)

    def __contains__(self, key):
        return key in self._mapping

    def __getitem__(self, key):
        return self._mapping[key]

    def __hash__(self):
        return hash(frozenset(self._mapping.iteritems()))

    @property
    def name(self):
        return self._name

    @property
    def domain(self):
        return self._domain

    def get_value(self, atom, domain):
        return self[tuple(inp.get_value(atom, domain) for inp in self._inputs)]

# TODO: derive Gamble and Event from Func

class Gamble(collections.Mapping, collections.Hashable, cdd.NumberTypeable):
    """An immutable gamble.

    >>> pspace = PSpace('abc')
    >>> Gamble(pspace, {'a': 1, 'b': 4, 'c': 8}).number_type
    'float'
    >>> Gamble(pspace, [1, 2, 3]).number_type
    'float'
    >>> Gamble(pspace, {'a': '1/7', 'b': '4/3', 'c': '8/5'}).number_type
    'fraction'
    >>> Gamble(pspace, ['1', '2', '3/2']).number_type
    'fraction'
    >>> f1 = Gamble(pspace, {'a': 1, 'b': 4, 'c': 8}, number_type='fraction')
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
    >>> [f1 * 2, f1 + 2, f1 - 2] == [2 * f1, 2 + f1, -(2 - f1)]
    True
    >>> f2 = Gamble(pspace, {'a': 5, 'b': 8, 'c': 7}, number_type='fraction')
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
    >>> print(f1 / event) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: ...
    >>> [f1 * event, f1 + event] == [event * f1, event + f1]
    True
    >>> print(event - f1)
    a : 0
    b : -4
    c : -7
    """
    def __init__(self, pspace, data, number_type=None):
        """Construct a gamble on the given possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param data: The specification of a gamble, or a constant.
        :type data: |gambletype|
        :param number_type: The type to use for numbers: ``'float'``
            or ``'fraction'``. If omitted, then
            :func:`~cdd.get_number_type_from_sequences` is used to
            determine the number type.
        :type number_type: :class:`str`
        """
        self._pspace = PSpace.make(pspace)
        if isinstance(data, collections.Mapping):
            if number_type is None:
                cdd.NumberTypeable.__init__(
                    self,
                    cdd.get_number_type_from_sequences(data.itervalues()))
            else:
                cdd.NumberTypeable.__init__(self, number_type)
            self._data = dict((omega, self.make_number(data.get(omega, 0)))
                              for omega in self.pspace)
        elif isinstance(data, collections.Sequence):
            if len(data) < len(self.pspace):
                raise ValueError("data sequence too short")
            if number_type is None:
                cdd.NumberTypeable.__init__(
                    self,
                    cdd.get_number_type_from_sequences(data))
            else:
                cdd.NumberTypeable.__init__(self, number_type)
            self._data = dict((omega, self.make_number(value))
                              for omega, value
                              in itertools.izip(self.pspace, data))
        elif isinstance(data, numbers.Real):
            if number_type is None:
                cdd.NumberTypeable.__init__(
                    self,
                    cdd.get_number_type_from_value(data))
            else:
                cdd.NumberTypeable.__init__(self, number_type)
            self._data = dict((omega, self.make_number(data))
                              for omega in self.pspace)
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
        >>> Gamble([2, 3, 4], {2: 1, 3: 4, 4: 8}, number_type='float') # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace([2, 3, 4]),
               mapping={2: 1.0,
                        3: 4.0,
                        4: 8.0})
        >>> Gamble([2, 3, 4], {2: '2/6', 3: '4.0', 4: 8}, number_type='fraction') # doctest: +NORMALIZE_WHITESPACE
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
        >>> print(Gamble(pspace, {'rain': -14, 'sun': 4, 'clouds': 20}, number_type='float'))
        rain   : -14.0
        sun    : 4.0
        clouds : 20.0
        """
        return _str_keys_values(
            self.pspace,
            (self.number_str(value) for value in self.itervalues()))

    def _scalar(self, other, oper):
        """
        :raises: :exc:`~exceptions.TypeError` if other is not a scalar
        """
        other = self.make_number(other)
        return Gamble(self.pspace,
                      [oper(value, other) for value in self.itervalues()],
                      number_type=self.number_type)

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
                number_type=self.number_type)
        elif isinstance(other, Event):
            return self._pointwise(
                other.indicator(number_type=self.number_type), oper)
        else:
            # will raise a type error if operand is not scalar
            return self._scalar(other, oper)

    __add__ = lambda self, other: self._pointwise(other, self.NumberType.__add__)
    __sub__ = lambda self, other: self._pointwise(other, self.NumberType.__sub__)
    __mul__ = lambda self, other: self._pointwise(other, self.NumberType.__mul__)
    __truediv__ = lambda self, other: self._scalar(other, self.NumberType.__truediv__)

    def __neg__(self):
        return Gamble(self.pspace, [-value for value in self.itervalues()],
                      number_type=self.number_type)

    __radd__ = __add__
    __rsub__ = lambda self, other: self.__sub__(other).__neg__()
    __rmul__ = __mul__

    def minimum(self):
        """Find minimum value of the gamble."""
        return min(value for value in self.itervalues())

    def maximum(self):
        """Find maximum value of the gamble."""
        return max(value for value in self.itervalues())

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
    >>> Event(pspace, 'abz')
    Traceback (most recent call last):
        ...
    ValueError: event has element (z) not in possibility space
    """
    def __init__(self, pspace, data=False, name=None):
        """Construct an event on the given possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param data: The specification of an event.
        :type data: |eventtype|
        :param name: The name of the event (used for pretty printing).
        :type name: :class:`str`
        """
        def validated(omega):
            if omega in pspace:
                return omega
            else:
                raise ValueError(
                    "event has element ({0}) not in possibility space"
                    .format(omega))
        self._pspace = PSpace.make(pspace)
        if isinstance(data, collections.Iterable):
            self._data = frozenset(validated(omega) for omega in data)
        elif data is True:
            self._data = frozenset(self.pspace)
        elif data is False:
            self._data = frozenset()
        else:
            raise TypeError("specify data as iterable, True, or False")
        if name is not None:
            self._name = name
        else:
            self._name = "(" + ",".join(str(omega) for omega in self) + ")"

    @property
    def pspace(self):
        """An :class:`~improb.PSpace` representing the possibility space."""
        return self._pspace

    @property
    def name(self):
        return self._name

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
        return _str_keys_values(
            self.pspace,
            (1 if omega in self else 0 for omega in self.pspace))

    def complement(self):
        """Calculate the complement of the event.

        >>> print(Event(pspace='abcde', data='bde').complement())
        a : 1
        b : 0
        c : 1
        d : 0
        e : 0

        :return: Complement.
        :rtype: :class:`Event`
        """
        return Event(self.pspace, True) - self

    def indicator(self, number_type=None):
        """Return indicator gamble for the event.

        :param number_type: The number type (defaults to ``'float'``
            if omitted).
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
        >>> event.indicator() # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace(5),
               mapping={0: 0.0,
                        1: 0.0,
                        2: 1.0,
                        3: 0.0,
                        4: 1.0})
        """
        if number_type is None:
            # float is default
            number_type = 'float'
        return Gamble(self.pspace,
                      dict((omega, 1 if omega in self else 0)
                           for omega in self.pspace),
                      number_type=number_type)

    def is_true(self):
        return len(self) == len(self.pspace)

    def is_false(self):
        return len(self) == 0

    def is_singleton(self):
        return len(self) == 1

    def __sub__(self, other):
        # override this to make sure we only do set difference!
        if isinstance(other, collections.Set):
            return collections.Set.__sub__(self, other)
        else:
            # e.g. a Gamble: will be handled by Gamble.__rsub__
            return NotImplemented
