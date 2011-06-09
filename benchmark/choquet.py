# benchmark script for Choquet integration

from collections import defaultdict
import random
import time

from improb import PSpace
from improb.setfunction import SetFunction

def timeit(n=10, m=10):
    k = 10000 // n # number of trials, for timing

    gambles = [
        dict((i, random.randint(1, m))
             for i in xrange(n))
        for j in xrange(k)]

    pspace = PSpace(n)
    s = SetFunction(
        pspace=pspace,
        number_type='fraction')
    # hack so we do not need to fill the set function with data
    # (this solves issues when testing for large n)
    s._data = defaultdict(lambda: random.randint(-len(pspace), len(pspace)))

    t = time.clock()
    for gamble in gambles:
        s.get_choquet(gamble)
    return time.clock() - t

for n in [2, 8, 32, 256]:
    for m in [1, 2, 4, 8, 32, 256, 65536]:
        print("n={0:<3} m={1:<5} t={2:<5.3g}"
              .format(n, m, timeit(n, m)))
