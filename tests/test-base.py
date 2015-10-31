import os
import sys
import tarfile

from Queue import Queue
# from datetime import datetime

import mock
try:
    import unittest2
except ImportError:
    if sys.version_info < (2, 7):
        raise
    import unittest as unittest2

from dns.exception import DNSException

from sachannelupdate.exceptions import SaChannelUpdateError
from sachannelupdate.base import getfiles, create_file, deploy_file, package, \
    process, get_counter, update_dns


def stat_side_effects(*args):
    if args[0] == '/srv/www/saupdate/rule.cf':
        return mock.Mock(st_mtime=1)
    if args[0] == '/var/lib/saupdate/rule.cf':
        return mock.Mock(st_mtime=2)


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

    @mock.patch('sachannelupdate.base.open', create=True)
    def test_deploy_file(self, mock_open):
        source = '/tmp/rule1.cf'
        dest = '/srv/www/saupdate/rule1.cf'
        deploy_file(source, dest)
        expected_calls = [mock.call(source), mock.call(dest, 'w')]
        self.assertEqual(expected_calls, mock_open.call_args_list)

    @mock.patch('sachannelupdate.base.os.path.isfile')
    @mock.patch('sachannelupdate.base.os.listdir')
    @mock.patch('sachannelupdate.base.tarfile', spec=tarfile)
    @mock.patch('sachannelupdate.base.os.chdir')
    def test_package(
            self, mock_chdir, mock_tarfile, mock_listdir, mock_isfile):
        tardir = '/srv/www/saupdate'
        dest = '/var/lib/saupdate'
        p_version = '10'
        mock_listdir.return_value = ['rule.cf']
        tarfile = os.path.join(tardir, '%s.tar.gz' % p_version)
        package(dest, tardir, p_version)
        mock_chdir.assert_called_once_with(dest)
        mock_tarfile.open.assert_called_once_with(tarfile, mode='w:gz')
        mock_listdir.assert_called_once_with('.')
        mock_tarfile.open.return_value.add.assert_called_once_with('rule.cf')
        mock_tarfile.open.return_value.close.assert_called_once_with()

    @mock.patch('sachannelupdate.base.deploy_file')
    @mock.patch('sachannelupdate.base.os.path.exists')
    def test_process_does_not_exist(self, mock_exists, mock_deploy_file):
        rulefiles = Queue()
        dest = '/srv/www/saupdate'
        rulefiles.put('/var/lib/saupdate/rule.cf')
        mock_exists.return_value = False
        deploy = process(dest, rulefiles)
        mock_exists.assert_called_once_with('/srv/www/saupdate/rule.cf')
        self.assertEqual(deploy, True)

    @mock.patch('sachannelupdate.base.os.stat')
    @mock.patch('sachannelupdate.base.deploy_file')
    @mock.patch('sachannelupdate.base.os.path.exists')
    def test_process_exists(self, mock_exists, mock_deploy_file, mock_stat):
        rulefiles = Queue()
        dest = '/srv/www/saupdate'
        rulefile = '/var/lib/saupdate/rule.cf'
        destfile = '/srv/www/saupdate/rule.cf'
        rulefiles.put(rulefile)
        mock_stat.side_effect = stat_side_effects
        mock_exists.return_value = True
        deploy = process(dest, rulefiles)
        mock_exists.assert_called_once_with(destfile)
        expected_calls = [mock.call(rulefile), mock.call(destfile)]
        self.assertEqual(deploy, True)
        self.assertEqual(expected_calls, mock_stat.call_args_list)

    @mock.patch('sachannelupdate.base.create_file')
    @mock.patch('sachannelupdate.base.open')
    def test_get_counter_new(self, mock_open, mock_create_file):
        counterfile = 'counter'
        mock_open.side_effect = IOError(
            'file or directory %s not found' % counterfile)
        version = get_counter(counterfile)
        mock_open.assert_called_once_with(counterfile)
        mock_create_file.assert_called_once_with(counterfile, '1')
        self.assertEqual(version, 1)

    @mock.patch('sachannelupdate.base.create_file')
    @mock.patch('sachannelupdate.base.open')
    def test_get_counter_permission_error(self, mock_open, mock_create_file):
        counterfile = 'counter'
        mock_open.side_effect = OSError('permission denied')
        with self.assertRaises(SaChannelUpdateError) as cmo:
            get_counter(counterfile)
        mock_open.assert_called_once_with(counterfile)

    @mock.patch('sachannelupdate.base.open')
    def test_get_counter_permission_error(self, mock_open):
        counterfile = 'counter'
        mock_open.read.return_value = 1
        version = get_counter(counterfile)
        mock_open.assert_called_once_with(counterfile)
        self.assertEqual(version, 2)

    @mock.patch('sachannelupdate.base.query')
    @mock.patch('sachannelupdate.base.update')
    @mock.patch('sachannelupdate.base.tsigkeyring')
    def test_update_dns_ok(self, mock_tsigkeyring, mock_update, mock_query):
        record = 'update'
        sa_version = '3.4.1'
        config = dict(dns_key='6e2347bc-278e-42f6-a84b-fa1766140cbd')
        result = update_dns(config, record, sa_version)
        self.assertEqual(result, True)

    @mock.patch('sachannelupdate.base.query')
    @mock.patch('sachannelupdate.base.update')
    @mock.patch('sachannelupdate.base.tsigkeyring')
    def test_update_dns_error(self, mock_tsigkeyring, mock_update, mock_query):
        record = 'update'
        sa_version = '3.4.1'
        config = dict(dns_key='6e2347bc-278e-42f6-a84b-fa1766140cbd')
        mock_query.tcp.side_effect = DNSException('permission denied')
        with self.assertRaises(SaChannelUpdateError):
            update_dns(config, record, sa_version)
        # self.assertEqual(result, True)


if __name__ == "__main__":
    unittest2.main()
