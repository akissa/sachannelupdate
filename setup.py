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
import sys

from imp import load_source
from setuptools import setup, find_packages

INSTALL_REQUIRES = ['python-gnupg', 'dnspython', 'paramiko']
TESTS_REQUIRE = ['nose', 'mock']

if sys.version_info < (2, 7):
    TESTS_REQUIRE.append('unittest2')


def get_readme():
    """Generate long description"""
    pandoc = None
    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        pandoc = os.path.join(path, 'pandoc')
        if os.path.isfile(pandoc) and os.access(pandoc, os.X_OK):
            break
    try:
        if pandoc:
            cmd = [pandoc, '-t', 'rst', 'README.md']
            long_description = os.popen(' '.join(cmd)).read()
        else:
            raise ValueError
    except BaseException:
        long_description = open("README.md").read()
    return long_description


def main():
    """Main"""
    lic = (
        'License :: OSI Approved :: GNU Affero '
        'General Public License v3 or later (AGPLv3+)')
    version = load_source(
        "version", os.path.join("sachannelupdate", "__init__.py"))

    opts = dict(
        name="sachannelupdate",
        version=version.__version__,
        description=version.__description__,
        long_description=get_readme(),
        keywords="spam sa-update spamassassin sa-channel channels",
        author="Andrew Colin Kissa",
        author_email="andrew@topdog.za.net",
        url="https://github.com/akissa/sachannelupdate",
        license="AGPLv3+",
        packages=find_packages(exclude=['tests']),
        scripts=['bin/updatesachannel'],
        include_package_data=True,
        zip_safe=False,
        tests_require=TESTS_REQUIRE,
        install_requires=INSTALL_REQUIRES,
        classifiers=[
            'Development Status :: 4 - Beta',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Intended Audience :: System Administrators',
            'Topic :: System :: Software Distribution',
            lic,
            'Natural Language :: English',
            'Operating System :: OS Independent'],)
    setup(**opts)


if __name__ == "__main__":
    main()
