import sys

import mock
try:
    import unittest2
except ImportError:
    if sys.version_info < (2, 7):
        raise
    import unittest as unittest2


class CLITestCase(unittest2.TestCase):

    def test_main(self):
        pass


if __name__ == "__main__":
    unittest2.main()
