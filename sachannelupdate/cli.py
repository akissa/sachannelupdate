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
sachannelupdate: CLI functions
"""
import os

from optparse import OptionParser
from ConfigParser import ConfigParser

from sachannelupdate import entry, error, SaChannelUpdateConfigError


def main():
    """Main function"""
    parser = OptionParser()
    parser.add_option(
        '-c', '--config',
        help='configuration file',
        dest='filename',
        type='str',
        default='/etc/sachannelupdate/sachannelupdate.ini')
    parser.add_option(
        '-d', '--delete',
        help='Deletes existing rules',
        dest='cleanup',
        action="store_true",
        default=False,)
    options, _ = parser.parse_args()
    if not os.path.isfile(options.filename):
        raise SaChannelUpdateConfigError(
            "The configuration file: %s does not exist" % options.filename)

    config = ConfigParser()
    config.read(options.filename)
    try:
        # pylint: disable=protected-access
        entry(config._sections['settings'], options.cleanup)
    except BaseException as msg:
        error(msg)
