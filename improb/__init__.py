"""improb is a Python module for working with imprecise probabilities."""

__version__ = '0.1.0'

import collections
import itertools

def make_pspace(*args):
    """Convert *args* into a possibility space.

    :param args: The components of the space.
    :type args: :class:`Iterable` or ``int``
    :returns: A possibility space.
    :rtype: ``tuple``

    Some examples of how components can be specified:

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

    If multiple components are specified, the product is calculated:

    .. doctest::

       >>> improb.make_pspace(3, 'abc') # doctest: +NORMALIZE_WHITESPACE
       ((0, 'a'), (0, 'b'), (0, 'c'),
        (1, 'a'), (1, 'b'), (1, 'c'),
        (2, 'a'), (2, 'b'), (2, 'c'))

    It also removes duplicates:

    .. doctest::

       >>> improb.make_pspace([2, 2, 5])
       (2, 5)
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
    :rtype: ``dict``

    >>> pspace = improb.make_pspace(5)
    >>> improb.make_gamble(pspace, [1, 9, 2, 3, 6])
    {0: 1.0, 1: 9.0, 2: 2.0, 3: 3.0, 4: 6.0}
    """
    return dict((omega, float(mapping[omega])) for omega in pspace)

def make_event(pspace, elements):
    """Convert *elements* into an event on *pspace*.

    :returns: An event.
    :rtype: ``set``

    >>> pspace = improb.make_pspace(6)
    >>> improb.make_event(pspace, xrange(1, 4))
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
        >>> improb.PSpace([2, 4, 5])
        PSpace([2, 4, 5])
        """
        return "PSpace(%s)" % repr(list(self))

    def __str__(self):
        """
        >>> print(improb.PSpace([2, 4, 5]))
        2 4 5
        """
        return " ".join(str(omega) for omega in self)

    def subsets(self, event=None):
        r"""Iterates over all subsets of the possibility space.

        :param event: An event (optional).
        :type event: |eventtype|
        :returns: Yields all subsets.
        :rtype: Iterator of :class:`Event`.

        >>> pspace = improb.PSpace([2, 4, 5])
        >>> print("\n---\n".join(str(subset) for subset in in pspace.subsets()))
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
        >>> print("\n---\n".join(str(subset) for subset in in pspace.subsets([2, 4])))
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
    """An immutable gamble with syntactic sugar.

    >>> pspace = improb.PSpace('abc')
    >>> f1 = improb.Gamble(pspace, {'a': 1, 'b': 4, 'c': 8})
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
    >>> f2 = improb.Gamble(pspace, {'a': 5, 'b': 8, 'c': 7})
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
    >>> event = improb.Event(pspace, 'ac')
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
        if not isinstance(pspace, PSpace):
            raise TypeError(
                "first Gamble() argument must be a PSpace, not '%s'"
                % pspace.__class__)
        self._data = dict((omega, float(mapping[omega])) for omega in pspace)
        self._pspace = pspace

    @property
    def pspace(self):
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
        >>> pspace = improb.PSpace([2, 3, 4])
        >>> improb.Gamble(pspace, {2: 1, 3: 4, 4: 8})
        Gamble(pspace=PSpace([2, 3, 4]), mapping={2: 1.0, 3: 4.0, 4: 8.0})
        """
        return "Gamble(pspace={0}, mapping={1})".format(
            repr(self._pspace), repr(self._data))

    def __str__(self):
        """
        >>> pspace = improb.PSpace('rain sun clouds'.split())
        >>> print(improb.Gamble(pspace, {'rain': -14, 'sun': 4, 'clouds': 20}))
        rain   : -14.000
        sun    :   4.000
        clouds :  20.000
        """
        maxlen_pspace = max(len(str(omega)) for omega in self.pspace)
        maxlen_value = max(len("{0:.3f}".format(self[omega]))
                           for omega in self.pspace)
        return "\n".join(
            "{0: <{1}} : {2:{3}.3f}".format(
                omega, maxlen_pspace, self[omega], maxlen_value)
            for omega in self.pspace)

    def _scalar(self, other, oper):
        if isinstance(other, (int, long, float)):
            return Gamble(self.pspace,
                          dict((omega, oper(self[omega], other))
                               for omega in self.pspace))
        else:
            raise TypeError("argument must be a scalar, not '%s'"
                            % other.__class__)

    def _pointwise(self, other, oper):
        if isinstance(other, (int, long, float)):
            return self._scalar(other, oper)
        elif isinstance(other, Event):
            if self.pspace != other.pspace:
                raise ValueError("possibility spaces do not match")
            return Gamble(self.pspace,
                          dict((omega, oper(self[omega],
                                            1.0 if omega in other else 0.0))
                               for omega in self.pspace))
        elif isinstance(other, Gamble):
            if self.pspace != other.pspace:
                raise ValueError("possibility spaces do not match")
            return Gamble(self.pspace,
                          dict((omega, oper(self[omega], float(other[omega])))
                               for omega in self.pspace))

    __add__ = lambda self, other: self._pointwise(other, float.__add__)
    __sub__ = lambda self, other: self._pointwise(other, float.__sub__)
    __mul__ = lambda self, other: self._pointwise(other, float.__mul__)
    __div__ = lambda self, other: self._scalar(other, float.__div__)

class Event(collections.Set, collections.Hashable):
    """An immutable event with syntactic sugar.

    >>> pspace = improb.PSpace('abcdef')
    >>> event1 = improb.Event(pspace, 'acd')
    >>> print(event1)
    a : 1
    b : 0
    c : 1
    d : 1
    e : 0
    f : 0
    >>> event2 = improb.Event(pspace, 'cdef')
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
        if not isinstance(pspace, PSpace):
            raise TypeError(
                "first Event() argument must be a PSpace, not '%s'"
                % pspace.__class__)
        self._data = frozenset(omega for omega in pspace if omega in elements)
        self._pspace = pspace

    @property
    def pspace(self):
        """The possibility space on which the event is defined."""
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
        >>> pspace = improb.PSpace([2, 3, 4])
        >>> improb.Event(pspace, [3, 4])
        Event(pspace=PSpace([2, 3, 4]), elements=set([3, 4]))
        """
        return "Event(pspace=%s, elements=%s)" % (repr(self.pspace), repr(set(self)))

    def __str__(self):
        """
        >>> pspace = improb.PSpace('rain sun clouds'.split())
        >>> print(improb.Event(pspace, 'rain clouds'.split()))
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

        >>> pspace = improb.PSpace(5)
        >>> event = improb.Event(pspace, [2, 4])
        >>> event.indicator() # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace([0, 1, 2, 3, 4]),
               mapping={0: 0.0, 1: 0.0, 2: 1.0, 3: 0.0, 4: 1.0})
        """
        return Gamble(self.pspace, dict((omega, 1 if omega in self else 0)
                                        for omega in self.pspace))
