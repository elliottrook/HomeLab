import subprocess
import unittest
from unittest.mock import patch
from keychain_read import diagnose


class DiagnosticTests(unittest.TestCase):
    def test_supervised_mode_only_extends_private_read_deadline(self):
        result=subprocess.CompletedProcess([],0,b'fixture\n')
        with patch('keychain_read.subprocess.run',return_value=result) as run:
            summary=diagnose(supervised=True)
        self.assertEqual(run.call_args.kwargs['timeout'],90)
        self.assertEqual(summary['status'],'readable_valid_shape')
        self.assertEqual(summary['network_calls'],0)
        with patch('keychain_read.subprocess.run') as run:
            with self.assertRaises(ValueError):diagnose(supervised='yes')
            run.assert_not_called()

    def test_private_output_never_returned(self):
        result=subprocess.CompletedProcess([],0,b'fictional-private-value\n')
        with patch('keychain_read.subprocess.run',return_value=result) as run:
            summary=diagnose()
        self.assertEqual(summary['status'],'readable_valid_shape')
        self.assertNotIn('fictional-private',str(summary));self.assertEqual(result.stdout,b'')
        self.assertEqual(run.call_args.kwargs['timeout'],5)
        self.assertEqual(run.call_args.kwargs['stderr'],subprocess.DEVNULL)

    def test_failures_report_only_fixed_categories(self):
        for error,category in [(subprocess.TimeoutExpired('private-command',5,output=b'private'),
                                'keychain_read_timeout'),
                               (subprocess.CalledProcessError(1,'private-command',output=b'private'),
                                'keychain_read_denied_or_failed')]:
            with patch('keychain_read.subprocess.run',side_effect=error):summary=diagnose()
            self.assertEqual(summary['status'],category)
            self.assertNotIn('private',str(summary))
