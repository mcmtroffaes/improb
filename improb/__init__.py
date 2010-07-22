"""improb is a Python module for working with imprecise probabilities."""

__version__ = '0.0.0'

def make_pspace(arg=None):
    """Convert *arg* into a possibility space.

    :returns: A possibility space.
    :rtype: ``tuple``
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
    """
    return dict((omega, float(mapping[omega])) for omega in pspace)

def make_event(pspace, elements):
    """Convert *elements* into an event on *pspace*.

    :returns: An event.
    :rtype: ``set``
    """
    return set(omega for omega in pspace if omega in elements)
