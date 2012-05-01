"""Created own Testsuite for this test because it caused problems with other tests"""
import unittest2 as unittest
import doctest
from plone.testing import layered
from opengever.task.testing import OPENGEVER_TASK_INTEGRATION_TESTING


TESTFILES = (
    '../behaviors.txt',

    )


OPTIONFLAGS = (doctest.NORMALIZE_WHITESPACE |
               doctest.ELLIPSIS |
               doctest.REPORT_NDIFF)


def test_suite():

    suite = unittest.TestSuite()

    for testfile in TESTFILES:
        suite.addTests([
            layered(doctest.DocFileSuite(testfile,
                    optionflags=OPTIONFLAGS),
                    layer=OPENGEVER_TASK_INTEGRATION_TESTING),
        ])

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')