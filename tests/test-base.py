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


from sachannelupdate.base import getfiles, create_file


class BaseTestCase(unittest2.TestCase):

    @mock.patch('sachannelupdate.base.os.path.isfile')
    def test_get_files(self, mock_isfile):
        mock_isfile.return_value = True
        cffiles = Queue()
        dirname = '/srv/www/saupdate'
        names = ['rules.cf']
        getfiles(cffiles, dirname, names)
        lfilename = os.path.join(dirname, names[0])
        mock_isfile.assert_called_once_with(lfilename)
        self.assertEqual(lfilename, cffiles.get())

    @mock.patch('sachannelupdate.base.open')
    def test_create_file(self, mock_open):
        name = 'rules.cf'
        content = 'xs1'
        create_file(name, content)
        mock_open.assert_called_once_with(name, 'w')
