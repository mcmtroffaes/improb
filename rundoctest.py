# run all doctests in the improb package

import doctest, unittest
import improb
import improb.lowprev
import improb.decision

# modules

suite = unittest.TestSuite()
for mod in [improb, improb.lowprev, improb.decision]:
    try:
        suite.addTest(doctest.DocTestSuite(mod))
    except ValueError: # no tests
        pass

# examples

suite.addTest(doctest.DocFileSuite('examples/frechet.txt'))

# regression tests

suite.addTest(doctest.DocFileSuite('tests/lowprev.txt'))

runner = unittest.TextTestRunner(verbosity=10)
runner.run(suite)

