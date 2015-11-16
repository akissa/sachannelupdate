import os
import sys

from Queue import Queue
from pwd import getpwuid

import mock
try:
    import unittest2
except ImportError:
    if sys.version_info < (2, 7):
        raise
    import unittest as unittest2


from sachannelupdate.transports import get_key_files, get_ssh_keys, \
    get_remote_path, get_ssh_dir, get_local_user, get_host_keys, \
    get_sftp_conn


class TransportsTestCase(unittest2.TestCase):

    @mock.patch('sachannelupdate.transports.os.path.isfile')
    def test_get_key_files(self, mock_isfile):
        mock_isfile.return_value = True
        keys = Queue()
        dirname = '/home/andrew/.ssh'
        names = ['id_rsa']
        get_key_files(keys, dirname, names)
        lfilename = os.path.join(dirname, names[0])
        mock_isfile.assert_called_once_with(lfilename)
        self.assertEqual(lfilename, keys.get())

    @mock.patch('sachannelupdate.transports.Queue')
    @mock.patch('sachannelupdate.transports.os.path.isfile')
    @mock.patch('sachannelupdate.transports.os.walk')
    def test_get_ssh_keys(self, mock_walk, mock_isfile, mock_queue):
        path = '/home/andrew/.ssh'
        mock_isfile.return_value = True
        mock_walk.return_value = [
            (path, (), ('id_rsa', 'id_rsa.pub'))
        ]
        get_ssh_keys(path)
        self.assertTrue(mock_walk.called)
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_queue.return_value.put.called)

    @mock.patch('sachannelupdate.transports.Queue')
    @mock.patch('sachannelupdate.transports.os.path.isfile')
    @mock.patch('sachannelupdate.transports.os.walk')
    def test_get_ssh_keys_none(self, mock_walk, mock_isfile, mock_queue):
        path = '/home/andrew/.ssh'
        mock_isfile.return_value = True
        mock_walk.return_value = [
            (path, (), ())
        ]
        get_ssh_keys(path)
        self.assertTrue(mock_walk.called)
        self.assertFalse(mock_isfile.called)
        self.assertFalse(mock_queue.return_value.put.called)

    def test_get_remote_path(self):
        for path in [
            'sftp://127.0.0.1/srv/www/saupdate',
                'sftp://192.168.1.25:22/srv/www/saupdate']:
            result = get_remote_path(path)
            self.assertEqual(result, '/srv/www/saupdate')

    def test_get_ssh_dir(self):
        config = {}
        username = getpwuid(os.geteuid()).pw_name
        sshdir = os.path.join(getpwuid(os.geteuid()).pw_dir, '.ssh')
        if not os.path.isdir(sshdir):
            sshdir = None
        result = get_ssh_dir(config, username)
        self.assertEqual(result, sshdir)

    @mock.patch('sachannelupdate.transports.os.path.isdir')
    def test_get_ssh_dir_pwn(self, mock_isdir):
        config = {}
        mock_isdir.return_value = False
        username = getpwuid(os.geteuid()).pw_name
        sshdir = os.path.join(getpwuid(os.geteuid()).pw_dir, '.ssh')
        if not os.path.isdir(sshdir):
            sshdir = None
        result = get_ssh_dir(config, username)
        self.assertEqual(result, sshdir)

    def test_get_local_user(self):
        result = get_local_user('tony')
        self.assertEqual(result, getpwuid(os.geteuid()).pw_name)
        result = get_local_user(getpwuid(os.geteuid()).pw_name)
        self.assertEqual(result, getpwuid(os.geteuid()).pw_name)

    def test_get_host_keys(self):
        sshdir = os.path.dirname(__file__)
        key = get_host_keys('secure.example.com', sshdir)
        self.assertTrue(key is not None)
        key = get_host_keys('test.example.com', sshdir)
        self.assertTrue(key is None)

    def test_get_host_keys_exp(self):
        sshdir = os.path.dirname(os.path.dirname(__file__))
        key = get_host_keys('secure.example.com', sshdir)
        self.assertTrue(key is None)

    def test_get_sftp_conn(self):
        pass


if __name__ == "__main__":
    unittest2.main()
