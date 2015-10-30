from __future__ import print_function
import sys

import mock
try:
    import unittest2
except ImportError:
    if sys.version_info < (2, 7):
        raise
    import unittest as unittest2

from sachannelupdate.utils import error, info


class UtilsTestCase(unittest2.TestCase):

    @mock.patch('sachannelupdate.utils.print')
    def test_error(self, mock_print):
        msg = "This is a sample error msg"
        error(msg)
        mock_print.assert_called_once_with(msg, file=sys.stderr)

    @mock.patch('sachannelupdate.utils.print')
    def test_info(self, mock_print):
        msg = "This is a sample msg"
        info(msg)
        mock_print.assert_called_once_with(msg, file=sys.stdout)
