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
sachannelupdate: Transports
"""
import os

from Queue import Queue
from pwd import getpwnam
from getpass import getuser
from urlparse import urlparse

from paramiko.util import load_host_keys
from paramiko import Transport, SFTPClient, PKey, PasswordRequiredException, \
    SSHException

from sachannelupdate.exceptions import SaChannelUpdateTransportError


def get_key_files(kfiles, dirname, names):
    """Return key files"""
    for name in names:
        fullname = os.path.join(dirname, name)
        if os.path.isfile(fullname) and \
            fullname.endswith('_rsa') or \
                fullname.endswith('_dsa'):
            kfiles.put(fullname)


def get_ssh_keys(sshdir):
    """Get SSH keys"""
    keys = Queue()
    os.path.walk(sshdir, get_key_files, keys)
    return keys


def get_remote_path(remote_location):
    """Get the remote path from the remote location"""
    parts = urlparse(remote_location)
    return parts.path


def get_ssh_dir(config, username):
    """Get the users ssh dir"""
    sshdir = config.get('ssh_config_dir')
    if not sshdir:
        sshdir = os.path.expanduser('~/.ssh')
        if not os.path.isdir(sshdir):
            pwentry = getpwnam(username)
            sshdir = os.path.join(pwentry.pw_dir, '.ssh')
            if not os.path.isdir(sshdir):
                sshdir = None
    return sshdir


def get_local_user(username):
    """Get the local username"""
    try:
        _ = getpwnam(username)
        luser = username
    except KeyError:
        luser = getuser()
    return luser


def get_host_keys(hostname, sshdir):
    """get host key"""
    hostkey = None
    # hostkeytype = None

    try:
        host_keys = load_host_keys(os.path.join(sshdir, 'known_hosts'))
    except IOError:
        host_keys = {}

    if hostname in host_keys:
        hostkeytype = host_keys[hostname].keys()[0]
        hostkey = host_keys[hostname][hostkeytype]

    return hostkey


def get_sftp_conn(config):
    """Make a SFTP connection, returns sftp client and connection objects"""
    remote = config.get('remote_location')
    parts = urlparse(remote)

    if ':' in parts.netloc:
        hostname, port = parts.netloc.split(':')
    else:
        hostname = parts.netloc
        port = 22
    port = int(port)

    username = config.get('remote_username') or getuser()
    luser = get_local_user(username)
    sshdir = get_ssh_dir(config, luser)
    hostkey = get_host_keys(hostname, sshdir)

    try:
        sftp = None
        keys = get_ssh_keys(sshdir)
        transport = Transport((hostname, port))
        while not keys.empty():
            try:
                key = PKey.from_private_key_file(keys.get())
                transport.connect(
                    hostkey=hostkey,
                    username=username,
                    password=None,
                    pkey=key)
                sftp = SFTPClient.from_transport(transport)
                break
            except (PasswordRequiredException, SSHException):
                pass
        if sftp is None:
            raise SaChannelUpdateTransportError("SFTP connection failed")
        return sftp, transport
    except BaseException as msg:
        raise SaChannelUpdateTransportError(msg)
