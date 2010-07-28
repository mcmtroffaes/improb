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

class PSpace(collections.Set, collections.Hashable):
    """An immutable possibility space with syntactic sugar, derived
    from :class:`collections.Set` and :class:`collections.Hashable`.
    """

    def __init__(self, *args):
        self.data = make_pspace(*args)

    def __len__(self):
        return len(self.data)

    def __contains__(self, omega):
        return omega in self.data

    def __iter__(self):
        return iter(self.data)

    def __hash__(self):
        return hash(self.data)

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
        """Iterates over all subsets of the possibility space.

        :param event: An event (optional).
        :type event: |eventtype|
        :returns: Yields all subsets.
        :rtype: Iterator of ``frozenset`` s.

        >>> pspace = improb.PSpace([2, 4, 5])
        >>> [subset for subset in pspace.subsets()] # doctest: +NORMALIZE_WHITESPACE
        [frozenset([]), frozenset([2]), frozenset([4]), frozenset([5]), 
         frozenset([2, 4]), frozenset([2, 5]), frozenset([4, 5]), 
         frozenset([2, 4, 5])]
        >>> [subset for subset in pspace.subsets([2, 4])]
        [frozenset([]), frozenset([2]), frozenset([4]), frozenset([2, 4])]
        """
        if event is None:
            event = self
        elif not isinstance(event, set):
            event = make_event(self, event)
        for subset_size in xrange(len(event) + 1):
            for subset in itertools.combinations(event, subset_size):
                yield frozenset(subset)

class Gamble(dict):
    """A gamble with syntactic sugar.

    >>> pspace = improb.PSpace(3)
    >>> f1 = improb.Gamble(pspace, {0: 1, 1: 4, 2: 8})
    >>> f1 + 2
    Gamble(pspace=PSpace([0, 1, 2]), mapping={0: 3.0, 1: 6.0, 2: 10.0})
    >>> f1 - 2
    Gamble(pspace=PSpace([0, 1, 2]), mapping={0: -1.0, 1: 2.0, 2: 6.0})
    >>> f1 * 2
    Gamble(pspace=PSpace([0, 1, 2]), mapping={0: 2.0, 1: 8.0, 2: 16.0})
    >>> f1 / 2
    Gamble(pspace=PSpace([0, 1, 2]), mapping={0: 0.5, 1: 2.0, 2: 4.0})
    >>> f2 = improb.Gamble(pspace, {0: 5, 1: 8, 2: 7})
    >>> f1 + f2
    Gamble(pspace=PSpace([0, 1, 2]), mapping={0: 6.0, 1: 12.0, 2: 15.0})
    >>> f1 - f2
    Gamble(pspace=PSpace([0, 1, 2]), mapping={0: -4.0, 1: -4.0, 2: 1.0})
    >>> f1 * f2 # doctest: +ELLIPSIS
    Gamble(pspace=PSpace([0, 1, 2]), mapping={0: 5.0, 1: 32.0, 2: 56.0})
    >>> f1 / f2 # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: ...
    >>> event = improb.Event(pspace, [0, 2])
    >>> f1 + event
    Gamble(pspace=PSpace([0, 1, 2]), mapping={0: 2.0, 1: 4.0, 2: 9.0})
    >>> f1 - event
    Gamble(pspace=PSpace([0, 1, 2]), mapping={0: 0.0, 1: 4.0, 2: 7.0})
    >>> f1 * event
    Gamble(pspace=PSpace([0, 1, 2]), mapping={0: 1.0, 1: 0.0, 2: 8.0})
    >>> f1 / event
    Traceback (most recent call last):
        ...
    TypeError: ...
    """
    def __init__(self, pspace, mapping):
        if not isinstance(pspace, PSpace):
            raise TypeError(
                "first Gamble() argument must be a PSpace, not '%s'"
                % pspace.__class__)
        dict.__init__(self,
                      ((omega, float(mapping[omega])) for omega in pspace))
        self.pspace = pspace

    def __repr__(self):
        """
        >>> pspace = improb.PSpace([2, 3, 4])
        >>> improb.Gamble(pspace, {2: 1, 3: 4, 4: 8})
        Gamble(pspace=PSpace([2, 3, 4]), mapping={2: 1.0, 3: 4.0, 4: 8.0})
        """
        return "Gamble(pspace=%s, mapping=%s)" % (repr(self.pspace), dict.__repr__(self))

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

class Event(set):
    """An event with syntactic sugar."""
    def __init__(self, pspace, elements):
        if not isinstance(pspace, PSpace):
            raise TypeError(
                "first Event() argument must be a PSpace, not '%s'"
                % pspace.__class__)
        set.__init__(self, (omega for omega in pspace if omega in elements))
        self.pspace = pspace

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

        >>> pspace = improb.PSpace(5)
        >>> event = improb.Event(pspace, [2, 4])
        >>> event.indicator() # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace([0, 1, 2, 3, 4]),
               mapping={0: 0.0, 1: 0.0, 2: 1.0, 3: 0.0, 4: 1.0})
        """
        return Gamble(self.pspace, dict((omega, 1 if omega in self else 0)
                                        for omega in self.pspace))
