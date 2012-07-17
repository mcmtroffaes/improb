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

# define a _make method to construct a flexible interface to various methods
class _Make:
    @classmethod
    def _make(cls, data):
        if isinstance(data, cls):
            return data
        else:
            return cls(data)

class Point(collections.Hashable, collections.Mapping, _Make):
    """A point. Basically, it is an immutable
    :class:`~collections.Mapping` from :class:`Var` instances to
    values.
    """

    def __init__(self, data):
        """Construct a point for the given *data*.

        :param data: A mapping from :class:`Var` instances to values.
        :type data: :class:`~collections.Mapping` (such as a :class:`dict`).
        :raises: ValueError, TypeError
        """

        if not isinstance(data, collections.Mapping):
            raise TypeError("expected a mapping")
        for var, value in data.iteritems():
            if not isinstance(var, Var):
                raise TypeError(
                    "expected Var key but got %s" % var.__class__.__name__)
            if not value in var:
                raise ValueError(
                    "%s not a value of %s" % (value, var))
        self._data = dict(data)

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __hash__(self):
        return hash(frozenset(self._data.iteritems()))

    def __str__(self):
        if len(self) >= 1:
            return (
                " & ".join(
                    "%s=%s" % (var.name, value)
                    for var, value in self._data.iteritems())
                )
        else:
            return "Ω"

    def __repr__(self):
        return "Point(%s)" % repr(self._data)

class Set(collections.Hashable, collections.Set, _Make):
    """An immutable mutually exclusive set of points."""

    def __init__(self, data):
        """Construct a set.

        :param data: The points of the set.
        :type data: :class:`collections.Iterable` of :class:`Point`\ s

        >>> a = Var([1, 2, 3])
        >>> s = Set([{a: 2}, {a: 3}])
        >>> {a: 1} in s
        False
        >>> {a: 2} in s
        True
        """

        if not isinstance(data, collections.Iterable):
            raise TypeError("expected an iterable")
        points = set()
        vars_ = set()
        for point in data:
            if not isinstance(point, Point):
                point = Point(point)
            points.add(point)
            vars_ |= set(point)
        # force canonical representation, so hash respects equality:
        # 1. ensure all points have the same domain
        # 2. remove unnecessary variables, i.e. use minimal representation
        # iterate over a copy of points because we may change it
        for point in list(points):
            extra_vars = tuple(vars_ - set(point))
            if extra_vars:
                points.remove(point)
                for values in itertools.product(*extra_vars):
                    point2 = dict(point)
                    point2.update(itertools.izip(extra_vars, values))
                    points.add(Point(point2))
        # iterate over a copy of vars_ because we may change it
        for var in list(vars_):
            # for speed: first check if all values are attained
            if set(var) == set(point[var] for point in points):
                # check if variable can be removed
                reduced_points = set() # points without var
                extra_points = set() # points with all values of var
                for point in points:
                    point2 = dict(point)
                    del point2[var]
                    reduced_points.add(Point(point2))
                    for value in var:
                        point2[var] = value
                        extra_points.add(Point(point2))
                if extra_points == points:
                    points = reduced_points
                    vars_.remove(var)
        self._domain = Domain(*vars_)
        self._points = frozenset(points)

    @property
    def domain(self):
        return self._domain

    def __len__(self):
        return len(self._points)

    def __iter__(self):
        return iter(self._points)

    def __contains__(self, point):
        point2 = dict(point)
        for var in list(point2):
            if var not in self._domain:
                del point2[var]
        # ensure equal domain for comparison
        extra_vars = tuple(self.domain - set(point2))
        if extra_vars:
            points3 = set()
            for values in itertools.product(*extra_vars):
                point3 = dict(point2)
                point3.update(itertools.izip(extra_vars, values))
                points3.add(Point(point3))
            return points3 <= self._points
        else:
            return Point(point2) in self._points

    def __hash__(self):
        return hash(self._points)

    def __str__(self):
        if len(self) >= 1:
            point_strs = [str(point) if len(point) <= 1 else "(%s)" % point
                          for point in self._points]
            return " | ".join(point_strs)
        else:
            return "∅"

    def __repr__(self):
        return "Set([%s])" % (", ".join(repr(point._data) for point in self._points))

    def points(self, domain):
        """Return a list of points relative to the given domain."""
        if not(domain >= self.domain):
            raise ValueError("domain too small, must also contain %s" % str(self.domain - domain))
        extra_vars = tuple(domain - self.domain)
        if extra_vars:
            for point in self:
                for values in itertools.product(*extra_vars):
                    point2 = dict(point)
                    point2.update(itertools.izip(extra_vars, values))
                    yield Point(point2)
        else:
            for point in self:
                yield point

    # we need to override more methods to get the right behaviour

    def __and__(self, other):
        if not isinstance(other, Set):
            if not isinstance(other, collections.Iterable):
                return NotImplemented
            other = self._from_iterable(other)
        dom = self.domain | other.domain
        self_points = set(self.points(dom))
        return self._from_iterable(
            point for point in other.points(dom) if point in self_points)

    def isdisjoint(self, other):
        if not isinstance(other, Set):
            if not isinstance(other, collections.Iterable):
                return NotImplemented
            other = self._from_iterable(other)
        dom = self.domain | other.domain
        self_points = set(self.points(dom))
        for point in other.points(dom):
            if point in self_points:
                return False
        return True

    def __sub__(self, other):
        if not isinstance(other, Set):
            if not isinstance(other, collections.Iterable):
                return NotImplemented
            other = self._from_iterable(other)
        dom = self.domain | other.domain
        return self._from_iterable(set(self.points(dom)) - set(other.points(dom)))

    def __le__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        dom = self.domain | other.domain
        return set(self.points(dom)) <= set(other.points(dom))

    # _abcoll.py implementation of Set.__or__ and Set.__xor__ work

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

class Domain(collections.Set):
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

    def size(self):
        """Number of points."""
        return reduce(operator.mul, (len(var) for var in self._vars))

    def __repr__(self):
        return (
            "%s(" % self.__class__.__name__
            + ", ".join(repr(var) for var in self._vars)
            + ")"
            )

    def __str__(self):
        return (
            " × ".join(
                "{" + ", ".join(str(val) for val in var) + "}"
                for var in self)
            )

    def subsets(self, event=None, empty=True, full=True,
                size=None, contains=None):
        """Iterates over all subsets of the possibility space.

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
        """

        if event is None:
            event = Set([{}]) # full space
        if contains is None:
            contains = Set([]) # empty set
        event = Set(event) if not isinstance(event, Set) else event
        contains = Set(contains) if not isinstance(contains, Set) else contains
        if not(contains <= event):
            # nothing to iterate over!!
            return
        extra_points = list((event - contains).points(self))
        if size is None:
            size_range = xrange(0 if empty else 1,
                                len(extra_points) + (1 if full else 0))
        elif isinstance(size, collections.Iterable):
            size_range = size
        elif isinstance(size, (int, long)):
            size_range = (size,)
        else:
            raise TypeError('invalid size')
        for subset_size in size_range:
            for subset in itertools.combinations(extra_points, subset_size):
                yield Set(subset) | contains

class MutableDomain(Domain, collections.MutableSet):

    __hash__ = None

    def add(self, var):
        if not isinstance(var, Var):
            raise TypeError("expected Var but got %s" % var.__class__.__name__)
        self._vars.add(var)

    def discard(self, var):
        self._vars.discard(var)

    # XXX Python bug? should investigate
    def __ge__(self, other):
        if not isinstance(other, collections.Set):
            return NotImplemented
        # other <= self, which is what _abcoll.py has,
        # is here _not_ the same
        # and apparently leads to self.__ge__(other) being called again???
        return other.__le__(self)

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

    __eq__ = lambda self, other: self.eq_(other).all()
    __ne__ = lambda self, other: self.ne_(other).any()
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

    def get_level_set(self, value):
        """Return :class:`Set` of points where the variable attains
        *value*.
        """
        return Set(
            point for point in self.domain.points()
            if self.get_value(point) == value)

    def get_level_sets(self):
        """Return :class:`~collections.Mapping` which maps values to sets."""
        level_sets = collections.defaultdict(list)
        for point in self.domain.points():
            level_sets[self.get_value(point)].append(point)
        return {value: Set(points) for value, points in level_sets.iteritems()}

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
        return self._name == other._name and self._values == other._values

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

    def __init__(self, inputs, data, name=None):
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
                mapping = {
                    (key,): value for key, value in data.iteritems()}
            else:
                self._inputs = tuple(inputs)
                mapping = dict(data)
        elif isinstance(data, collections.Sequence):
            if isinstance(inputs, ABCVar):
                self._inputs = (inputs,)
            else:
                self._inputs = tuple(inputs)
            mapping = dict(itertools.izip(
                itertools.product(*self._inputs), data))
        elif isinstance(data, collections.Callable):
            if isinstance(inputs, ABCVar):
                self._inputs = (inputs,)
            else:
                self._inputs = tuple(inputs)
            mapping = {
                key: data(*key) for key in itertools.product(*self._inputs)}
        else:
            raise TypeError(
                "expected collections.Mapping or collections.Sequence for data")
        if any(not isinstance(inp, ABCVar) for inp in self._inputs):
            raise TypeError("expected ABCVar or sequence of ABCVar for inputs")
        self._domain = functools.reduce(
            operator.or_, (inp.domain for inp in self._inputs))
        self._name = str(name) if name is not None else self._make_name()
        self._mapping = {}
        for point in self._domain.points():
            key = tuple(inp.get_value(point) for inp in self._inputs)
            self._mapping[key] = mapping[key]

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
        return hash(frozenset(
            (value, _points_hash(level_set))
            for value, level_set in self.get_level_sets().iteritems()))

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
