import unittest
from unittest.mock import patch
from conformance import run


class PortableConformanceTests(unittest.TestCase):
    def test_all_vectors_without_egress(self):
        with patch('socket.socket',side_effect=AssertionError('egress forbidden')),patch('subprocess.Popen',side_effect=AssertionError('process forbidden')):
            result=run()
        self.assertEqual(result['vector_count'],31)
        self.assertTrue(result['all_passed'])
        self.assertEqual(len({r['id'] for r in result['results']}),31)


if __name__=='__main__':unittest.main()
