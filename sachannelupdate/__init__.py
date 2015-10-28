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
from sachannelupdate.base import entry
from sachannelupdate.utils import error
from sachannelupdate.exceptions import SaChannelUpdateConfigError, \
    SaChannelUpdateError


# pylint: disable=bad-builtin
VER = (0, 0, 7)
__author__ = "Andrew Colin Kissa"
__copyright__ = u"© 2015 Andrew Colin Kissa"
__email__ = "andrew@topdog.za.net"
__description__ = "Utility for pushing updates to Spamassassin update channels"
__version__ = ".".join(map(str, VER))


assert entry
assert error
assert SaChannelUpdateError
assert SaChannelUpdateConfigError
