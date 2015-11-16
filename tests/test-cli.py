import os
import sys

import mock
try:
    import unittest2
except ImportError:
    if sys.version_info < (2, 7):
        raise
    import unittest as unittest2

from sachannelupdate.cli import main
from sachannelupdate.exceptions import SaChannelUpdateConfigError


class CLITestCase(unittest2.TestCase):

    def test_main_no_cf(self):
        default_cfg = '/etc/sachannelupdate/sachannelupdate.ini'
        sys.argv = ['__main__', '-c', default_cfg]
        with self.assertRaises(SaChannelUpdateConfigError) as cma:
            main()
            self.assertEqual(
                cma.exception.message,
                'The configuration file: %s does not exist' % default_cfg
            )

    @mock.patch('sachannelupdate.cli.entry')
    def test_main_cf(self, mock_entry):
        config = os.path.join(os.path.dirname(__file__), 'sa.ini')
        sys.argv = ['__main__', '-c', config]
        main()
        self.assertTrue(mock_entry.called)

    # @mock.patch('sachannelupdate.cli.entry')
    # def test_main_bad_cf(self, mock_entry):
    #     config = os.path.join(
    #         os.path.dirname(__file__),
    #         'bad-sachannelupdate.ini'
    #     )
    #     sys.argv = ['__main__', '-c', config]
    #     # with self.assertRaises(BaseException) as cma:
    #     main()
    #     # self.assertTrue(mock_entry.called)


if __name__ == "__main__":
    unittest2.main()
