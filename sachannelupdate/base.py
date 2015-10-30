# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
# sachannelupdate - Utility for pushing updates to Spamassassin update channels
# Copyright (C) 2015  Andrew Colin Kissa <andrew@topdog.za.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
sachannelupdate: Utility for pushing updates to Spamassassin update channels
Copyright (C) 2015  Andrew Colin Kissa <andrew@topdog.za.net>
"""
import os
import hashlib
import tarfile
import datetime

import gnupg

from Queue import Queue
from datetime import datetime

from dns.exception import DNSException
from dns import tsig, query, tsigkeyring, update

from sachannelupdate.exceptions import SaChannelUpdateConfigError \
    as CfgError, SaChannelUpdateDNSError, SaChannelUpdateError
from sachannelupdate.transports import get_sftp_conn, get_remote_path

BLOCKSIZE = 65536
HASHTMPL = """%s  %s\n"""


def create_file(name, content):
    "Generic to write file"
    with open(name, 'w') as writefile:
        writefile.write(content)


def getfiles(qfiles, dirname, names):
    """Get rule files in a directory"""
    for name in names:
        fullname = os.path.join(dirname, name)
        if os.path.isfile(fullname) and \
            fullname.endswith('.cf') or \
                fullname.endswith('.post'):
            qfiles.put(fullname)


def deploy_file(source, dest):
    """Deploy a file"""
    date = datetime.utcnow().strftime('%Y-%m-%d')
    shandle = open(source)
    with open(dest, 'w') as handle:
        for line in shandle:
            if line == '# Updated: %date%\n':
                newline = '# Updated: %s\n' % date
            else:
                newline = line
            handle.write(newline)
            handle.flush()
    shandle.close()


def package(dest, tardir, p_version):
    """Package files"""
    os.chdir(dest)
    p_filename = '%s.tar.gz' % p_version
    p_path = os.path.join(tardir, p_filename)
    tar = tarfile.open(p_path, mode='w:gz')
    for cf_file in os.listdir('.'):
        if os.path.isfile(cf_file):
            tar.add(cf_file)
    tar.close()


def process(dest, rulefiles):
    """process rules"""
    deploy = False
    while not rulefiles.empty():
        rulefile = rulefiles.get()
        base = os.path.basename(rulefile)
        dest = os.path.join(dest, base)
        if os.path.exists(dest):
            # check if older
            oldtime = os.stat(rulefile).st_mtime
            newtime = os.stat(dest).st_mtime
            if oldtime > newtime:
                deploy = True
                deploy_file(rulefile, dest)
        else:
            deploy = True
            deploy_file(rulefile, dest)
    return deploy


def get_counter(counterfile):
    """Get the counter value"""
    try:
        version_num = open(counterfile).read()
        version_num = int(version_num) + 1
    except (ValueError, IOError):
        version_num = 1
        create_file(counterfile, "%d" % version_num)
    except BaseException as msg:
        raise SaChannelUpdateError(msg)
    return version_num


def update_dns(config, record, sa_version):
    "Update the DNS record"
    try:
        domain = config.get('domain_name', 'sa.baruwa.com.')
        dns_key = config.get('domain_key')
        dns_ip = config.get('domain_ip', '127.0.0.1')
        keyring = tsigkeyring.from_text({domain: dns_key})
        transaction = update.Update(
            domain,
            keyring=keyring,
            keyalgorithm=tsig.HMAC_SHA512)
        txtrecord = '%s.%s' % (sa_version, domain)
        transaction.replace(txtrecord, 120, 'txt', record)
        query.tcp(transaction, dns_ip)
        return True
    except DNSException, msg:
        raise SaChannelUpdateDNSError(msg)


def sign(config, s_filename):
    """sign the package"""
    gpg_home = config.get(
        'settings', 'gpg_dir', '/var/lib/sachannelupdate/gnupg')
    gpg_pass = config.get('settings', 'gpg_passphrase')
    gpg_keyid = config.get('settings', 'gpg_keyid')
    gpg = gnupg.GPG(gnupghome=gpg_home)
    try:
        plaintext = open(s_filename, 'rb')
        signature = gpg.sign_file(
            plaintext, keyid=gpg_keyid, passphrase=gpg_pass, detach=True)
        with open('%s.asc' % s_filename, 'wb') as handle:
            handle.write(str(signature))
    finally:
        if 'plaintext' in locals():
            plaintext.close()


def hash_file(tar_filename):
    """hash the file"""
    hasher = hashlib.sha1()
    with open(tar_filename, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    data = HASHTMPL % (hasher.hexdigest(), os.path.basename(tar_filename))
    create_file('%s.sha1' % tar_filename, data)


def upload(config, remote_loc, u_filename):
    """Upload the files"""
    rcode = False
    try:
        sftp, transport = get_sftp_conn(config)
        remote_dir = get_remote_path(remote_loc)
        for part in ['sha1', 'asc']:
            local_file = '%s.%s' % (u_filename, part)
            remote_file = os.path.join(remote_dir, local_file)
            sftp.put(local_file, remote_file)
        sftp.put(remote_dir, os.path.join(remote_dir, u_filename))
        rcode = True
    except BaseException:
        pass
    finally:
        if 'transport' in locals():
            transport.close()
    return rcode


def cleanup(dest, tardir, counterfile):
    """Remove existing rules"""
    thefiles = Queue()
    os.path.walk(dest, getfiles, thefiles)
    for t_file in os.listdir(tardir):
        full_path = os.path.join(tardir, t_file)
        if os.path.isfile(full_path):
            thefiles.put(full_path)
    while not thefiles.empty():
        d_file = thefiles.get()
        print "Deleting file: %s" % d_file
        os.unlink(d_file)
    if os.path.exists(counterfile):
        print "Deleting the counter file %s" % counterfile
        os.unlink(counterfile)


def check_required(config):
    """Validate the input"""
    if config.get('domain_key') is None:
        raise CfgError("The domain_key option is required")
    if config.get('remote_loc') is None:
        raise CfgError("The remote_location option is required")
    if config.get('gpg_keyid') is None:
        raise CfgError("The gpg_keyid option is required")


def entry(config, delete_files=None):
    """Main function"""
    home_dir = config.get('home_dir', '/var/lib/sachannelupdate')
    dns_ver = config.get('spamassassin_version', '1.4.3')
    remote_loc = config.get('remote_location')
    home_dir = os.path.join(home_dir, 'rules')
    dest = os.path.join(home_dir, 'deploy')
    tardir = os.path.join(home_dir, 'archives')
    counterfile = os.path.join(home_dir, 'db', 'counters')

    check_required(config)

    if delete_files:
        cleanup(dest, tardir, counterfile)
        return

    cffiles = Queue()
    os.path.walk(home_dir, getfiles, cffiles)

    if process(dest, cffiles):
        version = get_counter(counterfile)
        filename = '%s.tar.gz' % version
        path = os.path.join(tardir, filename)
        package(dest, tardir, version)
        sign(config, path)
        hash_file(path)
        if upload(config, remote_loc, path) == 0:
            if update_dns(config, str(version), dns_ver):
                create_file(counterfile, "%d" % version)
