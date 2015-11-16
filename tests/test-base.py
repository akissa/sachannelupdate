import os
import sys
import tarfile

from Queue import Queue
from cStringIO import StringIO
# from datetime import datetime

import mock
try:
    import unittest2
except ImportError:
    if sys.version_info < (2, 7):
        raise
    import unittest as unittest2

from Queue import Queue
from StringIO import StringIO
from dns.exception import DNSException

from sachannelupdate.exceptions import SaChannelUpdateError, \
    SaChannelUpdateConfigError as CfgError
from sachannelupdate.base import getfiles, create_file, deploy_file, package, \
    process, get_counter, update_dns, sign, hash_file, HASHTMPL, upload, \
    queue_files, cleanup, check_required, get_cf_files, entry


R_FILES = ('70_baruwa.cf', '70_baruwa_dmarc.cf')
A_FILES = ('10.tar.gz', '10.tar.gz.asc', '10.tar.gz.sha1')
R_PATH = '/var/lib/sarulesupdate/deploy'
A_PATH = '/var/lib/sarulesupdate/archives'
CF_FILES = ('70_baruwa.cf', '70_baruwa.post', '70_baruwa.cf.orig')


def stat_side_effects(*args):
    if args[0] == '/srv/www/saupdate/rule.cf':
        return mock.Mock(st_mtime=1)
    if args[0] == '/var/lib/saupdate/rule.cf':
        return mock.Mock(st_mtime=2)


def queue_files_side_effects(*args):
    if args[0] == A_PATH:
        return [
            (args[0], (), A_FILES)
        ]
    elif args[0] == R_PATH:
        return [
            (args[0], (), R_FILES)
        ]
    else:
        raise ValueError(args[0])


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
    def test_get_counter_permission_oserror(self, mock_open, mock_create_file):
        counterfile = 'counter'
        mock_open.side_effect = OSError('permission denied')
        with self.assertRaises(SaChannelUpdateError):
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

    @mock.patch('sachannelupdate.base.open')
    @mock.patch('sachannelupdate.base.GPG')
    def test_sign(self, mock_gpg, mock_open):
        gpg_pass = 'xxxxxx'
        gpg_keyid = '01213'
        filename = '40.tar.gz'
        plaintext = 'testing rule'
        gpg_home = '/var/lib/sachannelupdate/gnupg'
        config = dict(gpg_passphrase=gpg_pass, gpg_keyid=gpg_keyid)
        mock_open.return_value.read.return_value = plaintext
        sign(config, filename)
        expected_calls = [
            mock.call(filename, 'rb'),
            mock.call('%s.asc' % filename, 'wb')
        ]
        mock_gpg.assert_called_once_with(gnupghome=gpg_home)
        mock_gpg.return_value.sign_file.assert_called_once_with(
            mock_open.return_value,
            keyid=gpg_keyid,
            passphrase=gpg_pass,
            detach=True)
        file_handle = mock_open.return_value.__enter__.return_value
        file_handle.write.assert_called_with(
            str(mock_gpg.return_value.sign_file.return_value)
        )
        mock_open.return_value.close.assert_called_once_with()
        self.assertEqual(expected_calls, mock_open.call_args_list)

    @mock.patch('sachannelupdate.base.create_file')
    @mock.patch('sachannelupdate.base.os')
    @mock.patch('sachannelupdate.base.sha1')
    def test_hash_file(self, mock_sha1, mock_os, mock_create_file):
        blocksize = 65536
        filename = '40.tar.gz'
        data = b"""score           RCVD_IN_BW_HKW                          -8.0
score           RCVD_IN_HOSTKARMA_W                     -5.0
score           RCVD_IN_BARUWAWL                        -5.0
"""
        eof = b''
        with mock.patch(
            'sachannelupdate.base.open',
            mock.mock_open(read_data=data),
                create=True) as mock_open:
            handle = mock_open.return_value.__enter__.return_value
            mock_open.return_value.__iter__.return_value = [data, eof]
            handle.read.side_effect = [data, eof]
            handle.read.return_value = [data, eof]
            mock_os.path.basename.return_value = filename
            mock_sha1.return_value.hexdigest.return_value = 'xxxxxxssasa'
            hash_file(filename)
            mock_sha1.assert_called_once_with()
            mock_open.assert_called_once_with(filename, 'rb')
            handle.read.assert_called_with(blocksize)
            self.assertTrue(len(handle.read.return_value) > 0)
            mock_sha1.return_value.update.assert_called_with(
                handle.read.return_value[0]
            )
            mock_sha1.return_value.hexdigest.assert_called_once_with()
            mock_os.path.basename.assert_called_once_with(filename)
            filedata = HASHTMPL % ('xxxxxxssasa', filename)
            mock_create_file.assert_called_once_with(
                '%s.sha1' % filename, filedata
            )
            self.assertTrue(mock_create_file.called)

    @mock.patch('sachannelupdate.base.os')
    @mock.patch('sachannelupdate.base.get_remote_path')
    @mock.patch('sachannelupdate.base.get_sftp_conn')
    def test_upload(self, mock_sftp_conn, mock_remote_path, mock_os):
        mock_sftp = mock.Mock()
        mock_transport = mock.Mock()
        mock_sftp_conn.return_value = [mock_sftp, mock_transport]
        self.assertTrue(upload(
            mock.sentinel.config,
            mock.sentinel.remote_loc,
            mock.sentinel.u_filename
        ))
        mock_sftp_conn.assert_called_once_with(mock.sentinel.config)
        mock_remote_path.assert_called_once_with(mock.sentinel.remote_loc)
        mock_transport.close.assert_called_once_with()
        self.assertEqual(mock_os.path.join.call_count, 3)

    @mock.patch('sachannelupdate.base.os')
    @mock.patch('sachannelupdate.base.get_remote_path')
    @mock.patch('sachannelupdate.base.get_sftp_conn')
    def test_upload_excp(self, mock_sftp_conn, mock_remote_path, mock_os):
        mock_sftp = mock.Mock()
        mock_transport = mock.Mock()
        mock_sftp.put.side_effect = ValueError()
        mock_sftp_conn.return_value = [mock_sftp, mock_transport]
        self.assertFalse(upload(
            mock.sentinel.config,
            mock.sentinel.remote_loc,
            mock.sentinel.u_filename
        ))
        mock_sftp_conn.assert_called_once_with(mock.sentinel.config)
        mock_remote_path.assert_called_once_with(mock.sentinel.remote_loc)
        mock_transport.close.assert_called_once_with()

    @mock.patch('sachannelupdate.base.os.walk')
    def test_queue_files(self, mock_walk):
        mock_queue = mock.Mock(spec=Queue)
        mock_walk.return_value = [
            (A_PATH, (), A_FILES)
        ]
        expected_calls = [
            mock.call('%s/%s' % (A_PATH, filename)) for filename in A_FILES
        ]
        queue_files(A_PATH, mock_queue)
        mock_walk.assert_called_once_with(A_PATH)
        self.assertTrue(mock_queue.put.called)
        self.assertEqual(expected_calls, mock_queue.put.call_args_list)

    @mock.patch('sachannelupdate.base.os.path.isfile')
    @mock.patch('sachannelupdate.base.os.walk')
    def test_get_cf_files(self, mock_walk, mock_isfile):
        mock_queue = mock.Mock(spec=Queue)
        mock_walk.return_value = [
            (R_PATH, (), CF_FILES)
        ]
        mock_isfile.return_value = True
        expected_calls = [
            mock.call('%s/%s' % (R_PATH, filename))
            for filename in CF_FILES
            if (filename.endswith('.cf') or filename.endswith('.post'))
        ]
        get_cf_files(R_PATH, mock_queue)
        mock_walk.assert_called_once_with(R_PATH)
        self.assertTrue(mock_queue.put.called)
        self.assertEqual(expected_calls, mock_queue.put.call_args_list)

    @mock.patch('sachannelupdate.base.os.unlink')
    @mock.patch('sachannelupdate.base.os.walk')
    @mock.patch('sachannelupdate.base.os.path.exists')
    def test_cleanup(self, mock_os_path_exists, mock_os_walk, mock_os_unlink):
        mock_os_path_exists.return_value = True
        mock_os_walk.side_effect = queue_files_side_effects
        counterfile = '/var/lib/sarulesupdate/db/counters'
        cleanup(R_PATH, A_PATH, counterfile)
        self.assertEqual(mock_os_unlink.call_count, 6)

    def test_check_required(self):
        config = {}
        with self.assertRaises(CfgError) as cma:
            check_required(config)
            self.assertEqual(
                cma.exception.message,
                'The domain_key option is required'
            )
        with self.assertRaises(CfgError) as cma:
            config['domain_key'] = mock.sentinel.domain_key
            check_required(config)
            self.assertEqual(
                cma.exception.message,
                'The remote_location option is required'
            )
        with self.assertRaises(CfgError) as cma:
            config['remote_loc'] = mock.sentinel.remote_loc
            check_required(config)
            self.assertEqual(
                cma.exception.message,
                'The gpg_keyid option is required'
            )

    # @mock.patch('sachannelupdate.base.os.path.isfile')
    # @mock.patch('sachannelupdate.base.os.walk')
    # def test_entry(self):
    #     config = dict(
    #         domain_key=mock.sentinel.domain_key,
    #         remote_loc=mock.sentinel.remote_loc,
    #         gpg_keyid=mock.sentinel.gpg_keyid,
    #     )
    #     mock_walk.return_value = [
    #         (R_PATH, (), CF_FILES)
    #     ]
    #     mock_isfile.return_value = True
    #     entry(config)


if __name__ == "__main__":
    unittest2.main()
