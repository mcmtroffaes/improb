# -*- coding: utf-8 -*-

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
import collections
import functools
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

def _points_hash(points):
    """Calculates hash value of a set that consists of the given
    sequence of mutually exclusive *points*. Equal subsets return the
    same hash value. This is a helper function for implementing hash
    calculations for various objects.
    """
    hash_ = hash(frozenset())
    vars_ = {}
    for point in points:
        for var, value in point.iteritems():
            assert isinstance(var, Var)
            if var not in vars_:
                vars_[var] = hash(var)
    visited = {var: set() for var in vars_}
    for point in points:
        for var, value in point.iteritems():
            assert value in var
            if value not in visited[var]:
                hash_ ^= hash((vars_[var], value))
                visited[var].add(value)
    for var, var_hash in vars_.iteritems():
        for value in var.itervalues():
            hash_ ^= hash((var_hash, value))
    return hash_

class Domain(collections.Hashable, collections.Set):
    """An immutable set of :class:`Var`\ s."""

    def __init__(self, *vars_):
        """Construct a domain for the given *vars_*.

        :param vars_: The components of the domain.
        :type vars_: Each component is a :class:`Var`.
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

    def points(self):
        """Generate all points of the domain."""
        for values in itertools.product(*self._vars):
            yield OrderedDict(itertools.izip(self._vars, values))

    def __repr__(self):
        return (
            "Domain("
            + ", ".join(repr(var) for var in self._vars)
            + ")"
            )

    def __str__(self):
        return (
            " × ".join(
                "{" + ", ".join(str(val) for val in var) + "}"
                for var in self)
            )

    def make_func(self, data):
        _vars = list(self._vars)[0] if len(self._vars) == 1 else self._vars
        if isinstance(data, ABCVar):
            return data
        elif isinstance(data, (collections.Mapping, collections.Sequence, collections.Callable)):
            return Func(_vars, data)
        elif isinstance(data, numbers.Real):
            return Func(_vars, lambda *key: data)
        else:
            raise TypeError(
                "cannot convert %s to ABCVar" % data.__class__.__name__)

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

        >>> a = Var([2, 4, 5])
        >>> pspace = Domain(a)
        >>> print("\n---\n".join(str(subset) for subset in pspace.subsets()))
        [2] : False
        [4] : False
        [5] : False
        ---
        [2] : True
        [4] : False
        [5] : False
        ---
        [2] : False
        [4] : True
        [5] : False
        ---
        [2] : False
        [4] : False
        [5] : True
        ---
        [2] : True
        [4] : True
        [5] : False
        ---
        [2] : True
        [4] : False
        [5] : True
        ---
        [2] : False
        [4] : True
        [5] : True
        ---
        [2] : True
        [4] : True
        [5] : True
        >>> print("\n---\n".join(str(subset) for subset in pspace.subsets(lambda x: x in [2, 4])))
        [2] : False
        [4] : False
        [5] : False
        ---
        [2] : True
        [4] : False
        [5] : False
        ---
        [2] : False
        [4] : True
        [5] : False
        ---
        [2] : True
        [4] : True
        [5] : False
        >>> print("\n---\n".join(str(subset) for subset in pspace.subsets(lambda x: x in [2, 4], empty=False, full=False)))
        [2] : True
        [4] : False
        [5] : False
        ---
        [2] : False
        [4] : True
        [5] : False
        >>> print("\n---\n".join(str(subset) for subset in pspace.subsets(True, contains=lambda x: x in [4])))
        [2] : False
        [4] : True
        [5] : False
        ---
        [2] : True
        [4] : True
        [5] : False
        ---
        [2] : False
        [4] : True
        [5] : True
        ---
        [2] : True
        [4] : True
        [5] : True
        """
        event = self.make_func(event).bool_()
        contains = self.make_func(contains).bool_()
        if not(contains <= event):
            # nothing to iterate over!!
            return
        length = len([point for point in self.points() if event.get_value(point)])
        if size is None:
            size_range = xrange(0 if empty else 1,
                                length + (1 if full else 0))
        elif isinstance(size, collections.Iterable):
            size_range = size
        elif isinstance(size, (int, long)):
            size_range = (size,)
        else:
            raise TypeError('invalid size')
        good_points = [
            point for point in self.points()
            if event.get_value(point) and not contains.get_value(point)]
        for subset_size in size_range:
            for subset in itertools.combinations(good_points, subset_size):
                yield Func(
                    self, {
                        tuple(point.itervalues()): (point in subset)
                        for point in self.points()}) | contains

class ABCVar(collections.Hashable, collections.Mapping):
    """Abstract base class for variables."""
    __metaclass__ = ABCMeta
    _nextid = 0

    @staticmethod
    def _make_name():
        name = "unnamed_{0}".format(ABCVar._nextid)
        ABCVar._nextid += 1
        return name

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
    def get_value(self, point):
        """Return value of this variable on *point*, relative to the
        given *domain*.

        :param point: An point.
        :type point: :class:`dict` from :class:`Var` to any value in :class:`Var`
        """
        raise NotImplementedError

    def points(self):
        """Generate all points of the domain where the variable
        evaluates to ``True``.
        """
        for point in self.domain.points():
            if self.get_value(point):
                yield point

    def __str__(self):
        return _str_keys_values(
            [point.values() for point in self.domain.points()],
            [self.get_value(point) for point in self.domain.points()]
            )

    def is_equivalent_to(self, other):
        """Check whether two variables are equivalent.

        :param other: The other variable.
        :type other: :class:`ABCVar`
        """
        domain = self.domain | other.domain
        for point in domain.points():
            if self.get_value(point) != other.get_value(point):
                return False
        return True

    def _scalar(self, other, oper):
        return Func(
            self,
            {value: oper(value, other) for value in self.itervalues()})

    def _pointwise(self, other, oper):
        if isinstance(other, ABCVar):
            return Func(
                [self, other],
                {(value, other_value): oper(value, other_value)
                 for value, other_value
                 in itertools.product(self.itervalues(), other.itervalues())}
                )
        else:
            # will raise a type error if operand is not scalar
            return self._scalar(other, oper)

    __add__ = lambda self, other: self._pointwise(other, operator.add)
    __sub__ = lambda self, other: self._pointwise(other, operator.sub)
    __mul__ = lambda self, other: self._pointwise(other, operator.mul)
    __truediv__ = lambda self, other: self._scalar(other, operator.truediv)
    __floordiv__ = lambda self, other: self._scalar(other, operator.floordiv)
    __div__ = lambda self, other: self._scalar(other, operator.div)
    __and__ = lambda self, other: self._pointwise(other, operator.and_)
    __or__ = lambda self, other: self._pointwise(other, operator.or_)
    __xor__ = lambda self, other: self._pointwise(other, operator.xor)

    def __invert__(self):
        return Func(self, {value: ~value for value in self.itervalues()})

    def __neg__(self):
        return Func(self, {value: -value for value in self.itervalues()})

    __radd__ = __add__
    __rsub__ = lambda self, other: self.__sub__(other).__neg__()
    __rmul__ = __mul__

    le_ = lambda self, other: self._pointwise(other, operator.le)
    lt_ = lambda self, other: self._pointwise(other, operator.lt)
    eq_ = lambda self, other: self._pointwise(other, operator.eq)
    ne_ = lambda self, other: self._pointwise(other, operator.ne)
    ge_ = lambda self, other: self._pointwise(other, operator.ge)
    gt_ = lambda self, other: self._pointwise(other, operator.gt)
    not_ = lambda self: Func(self, {value: not value for value in self.itervalues()})
    bool_ = lambda self: Func(self, {value: bool(value) for value in self.itervalues()})

    __le__ = lambda self, other: self.le_(other).all()
    __lt__ = lambda self, other: self.le_(other).all() and self.lt_(other).any()
    __ge__ = lambda self, other: self.ge_(other).all()
    __gt__ = lambda self, other: self.ge_(other).all() and self.gt_(other).any()

    def minimum(self):
        """Find minimum value of the gamble."""
        return min(value for value in self.itervalues())

    def maximum(self):
        """Find maximum value of the gamble."""
        return max(value for value in self.itervalues())

    # follow numpy convention
    def __nonzero__(self):
        raise ValueError("The truth value of a variable is ambiguous. Use a.any() or a.all()")

    all = lambda self: all(self.itervalues())
    any = lambda self: any(self.itervalues())

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

    def __eq__(self, other):
        return self._name == other._name and ABCVar.__eq__(self, other)

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

    def get_value(self, point):
        """
        >>> a = Var(range(3))
        >>> b = Var(['rain', 'sun'])
        >>> a.get_value({b: 'sun', a: 2})
        2
        >>> b.get_value({b: 'sun', a: 2})
        'sun'
        >>> b.get_value({b: 'blabla', a: 2}) # doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        KeyError: 'blabla'
        """
        # we could simply return point[self] but that might miss key errors
        return self[point[self]]

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
    >>> c = Func([a, b], [-1, 2, 0, 2])
    >>> print(c)
    [0, 'rain'] : -1
    [0, 'sun']  : 2
    [1, 'rain'] : 0
    [1, 'sun']  : 2
    >>> c = Func([a, b], lambda va, vb: 2 if vb == 'sun' else (va - 1))
    >>> print(c)
    [0, 'rain'] : -1
    [0, 'sun']  : 2
    [1, 'rain'] : 0
    [1, 'sun']  : 2
    >>> d = Func(c, {-1: False, 0: False, 2: True})
    >>> print(d)
    [0, 'rain'] : False
    [0, 'sun']  : True
    [1, 'rain'] : False
    [1, 'sun']  : True
    >>> e = Func(b, {'rain': False, 'sun': True})
    >>> e.is_equivalent_to(d)
    True
    >>> e.is_equivalent_to(a)
    False
    >>> print(b.eq_('rain'))
    ['rain'] : True
    ['sun']  : False
    >>> print(2 * b.eq_('rain'))
    ['rain'] : 2
    ['sun']  : 0
    >>> f = a + 2 * b.eq_('rain')
    >>> print(f)
    [0, 'rain'] : 2
    [0, 'sun']  : 0
    [1, 'rain'] : 3
    [1, 'sun']  : 1
    >>> print(f.reduced())
    [0, 'rain'] : 2
    [0, 'sun']  : 0
    [1, 'rain'] : 3
    [1, 'sun']  : 1
    """

    def __init__(self, inputs, data, name=None, validate=True):
        """Construct a function.

        :param inputs: The input variables.
        :type inputs: :class:`improb.ABCVar` if there is only one input,
            or iterable of :class:`improb.ABCVar`\ s.
        :param data: Either maps each combination of values of input
            variables to a value, or lists a value for each such combination,
            or provides a function to calculate the value from input
            variable values.
        :type data: :class:`collections.Mapping` or :class:`collections.Sequence` or :class:`collections.Callable`
        :param name: The name of this function.
        :type name: :class:`str`
        :param validate: Whether to validate the keys of the mapping.
        :type validate: :class:`bool`
        """
        if isinstance(data, collections.Mapping):
            if isinstance(inputs, ABCVar):
                self._inputs = (inputs,)
                self._mapping = {
                    (key,): value for key, value in data.iteritems()}
            else:
                self._inputs = tuple(inputs)
                self._mapping = dict(data)
        elif isinstance(data, collections.Sequence):
            if isinstance(inputs, ABCVar):
                self._inputs = (inputs,)
            else:
                self._inputs = tuple(inputs)
            self._mapping = dict(itertools.izip(
                itertools.product(*self._inputs), data))
        elif isinstance(data, collections.Callable):
            if isinstance(inputs, ABCVar):
                self._inputs = (inputs,)
            else:
                self._inputs = tuple(inputs)
            self._mapping = {
                key: data(*key) for key in itertools.product(*self._inputs)}
        else:
            raise TypeError(
                "expected collections.Mapping or collections.Sequence for data")
        if any(not isinstance(inp, ABCVar) for inp in self._inputs):
            raise TypeError("expected ABCVar or sequence of ABCVar for inputs")
        self._domain = functools.reduce(
            operator.or_, (inp.domain for inp in self._inputs))
        self._name = str(name) if name is not None else self._make_name()
        if validate:
            for point in self._domain.points():
                self.get_value(point)

    def reduced(self):
        return Func(
            self.domain, {
                tuple(point.itervalues()): self.get_value(point)
                for point in self.domain.points()})

    def __repr__(self):
        return (
            "Func({0}, {1}, name={2})"
            .format(repr(self._inputs), repr(self._mapping), repr(self._name))
            )

    def __len__(self):
        return len(self._mapping)

    def __iter__(self):
        return iter(self._mapping)

    def __contains__(self, key):
        return key in self._mapping

    def __getitem__(self, key):
        return self._mapping[key]

    def __hash__(self):
        return hash(tuple(
            self._inputs,
            frozenset(self._mapping.iteritems()),
            self._name))

    @property
    def name(self):
        return self._name

    @property
    def domain(self):
        return self._domain

    def get_value(self, point):
        return self[tuple(inp.get_value(point) for inp in self._inputs)]

"""
Tests for gambles.

.. doctest::

    >>> x = Var('abc')
    >>> f1 = Func(x, {'a': 1, 'b': 4, 'c': 8})
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
    >>> f2 = Gamble(x, {'a': 5, 'b': 8, 'c': 7}, number_type='fraction')
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

"""
Tests for events.

    >>> a = Var('abcdef')
    >>> event1 = a.in_('acd')
    >>> print(event1)
    a : 1
    b : 0
    c : 1
    d : 1
    e : 0
    f : 0
    >>> event2 = a.in_('cdef')
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
