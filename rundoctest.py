# run all doctests in the improb package

import doctest, unittest
import improb
import improb.lowprev

# modules

suite = unittest.TestSuite()
for mod in [improb, improb.lowprev]:
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

