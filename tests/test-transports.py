import os
import sys

from Queue import Queue

import mock
try:
    import unittest2
except ImportError:
    if sys.version_info < (2, 7):
        raise
    import unittest as unittest2


from sachannelupdate.transports import get_key_files


class TransportsTestCase(unittest2.TestCase):

    @mock.patch('sachannelupdate.transports.os.path.isfile')
    def test_get_files(self, mock_isfile):
        mock_isfile.return_value = True
        keys = Queue()
        dirname = '/home/andrew/.ssh'
        names = ['id_rsa']
        get_key_files(keys, dirname, names)
        lfilename = os.path.join(dirname, names[0])
        mock_isfile.assert_called_once_with(lfilename)
        self.assertEqual(lfilename, keys.get())
