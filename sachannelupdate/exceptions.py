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
sachannelupdate: Custom exceptions
"""


class SaChannelUpdateError(Exception):
    """SaChannelUpdateError Exceptions"""
    def __init__(self, message):
        """Init"""
        super(SaChannelUpdateError, self).__init__(message)


class SaChannelUpdateConfigError(SaChannelUpdateError):
    """Configuration Exceptions"""
    pass


class SaChannelUpdateDNSError(SaChannelUpdateError):
    """DNS Exceptions"""
    pass


class SaChannelUpdateTransportError(SaChannelUpdateError):
    """Transport Exceptions"""
    pass
