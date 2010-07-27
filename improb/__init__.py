"""improb is a Python module for working with imprecise probabilities."""

__version__ = '0.1.0'

import itertools

def make_pspace(arg=None):
    """Convert *arg* into a possibility space.

    :returns: A possibility space.
    :rtype: ``tuple``

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
    """
    if arg is None:
        return (0, 1)
    elif isinstance(arg, int):
        return tuple(xrange(arg))
    else:
        return tuple(arg)

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

class PSpace(tuple):
    """A possibility space with syntactic sugar."""
    def __new__(cls, arg=None):
        return tuple.__new__(cls, make_pspace(arg))

    def __repr__(self):
        return "PSpace(%s)" % tuple.__repr__(self)

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
    Gamble(pspace=PSpace((0, 1, 2)), mapping={0: 3.0, 1: 6.0, 2: 10.0})
    >>> f1 - 2
    Gamble(pspace=PSpace((0, 1, 2)), mapping={0: -1.0, 1: 2.0, 2: 6.0})
    >>> f1 * 2
    Gamble(pspace=PSpace((0, 1, 2)), mapping={0: 2.0, 1: 8.0, 2: 16.0})
    >>> f1 / 2
    Gamble(pspace=PSpace((0, 1, 2)), mapping={0: 0.5, 1: 2.0, 2: 4.0})
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
        return "Gamble(pspace=%s, mapping=%s)" % (repr(self.pspace), dict.__repr__(self))

    def _oper(self, other, oper):
        if isinstance(other, (int, long, float)):
            return Gamble(self.pspace,
                          dict((omega, oper(self[omega], other))
                               for omega in self.pspace))
        else:
            return Gamble(self.pspace,
                          dict((omega, oper(self[omega], other[omega]))
                               for omega in self.pspace))       

    __add__ = lambda self, other: self._oper(other, float.__add__)
    __sub__ = lambda self, other: self._oper(other, float.__sub__)
    __mul__ = lambda self, other: self._oper(other, float.__mul__)
    __div__ = lambda self, other: self._oper(other, float.__div__)

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
        return "Event(pspace=%s, elements=%s)" % (repr(self.pspace), set.__repr__(self))

    def indicator(self):
        """Return indicator gamble for the event.

        >>> pspace = improb.PSpace(5)
        >>> event = improb.Event(pspace, [2, 4])
        >>> event.indicator() # doctest: +NORMALIZE_WHITESPACE
        Gamble(pspace=PSpace((0, 1, 2, 3, 4)),
               mapping={0: 0.0, 1: 0.0, 2: 1.0, 3: 0.0, 4: 1.0})
        """
        return Gamble(self.pspace, dict((omega, 1 if omega in self else 0)
                                        for omega in self.pspace))
