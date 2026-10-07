import json
import unittest
from unittest.mock import patch, MagicMock
from broker_gate import BrokerGate


class BrokerGateTests(unittest.TestCase):
    def test_only_exact_true_response_permits(self):
        for response, expected in [
            ({'ok':True,'result':{'global_enabled':True}},True),
            ({'ok':True,'result':{'global_enabled':False}},False),
            ({'ok':True,'result':{'global_enabled':1}},False),
            ({'ok':False,'result':{'global_enabled':True}},False),
            ({'ok':True,'result':{'global_enabled':True,'extra':'ignored?'}},False)]:
            with self.subTest(response=response):
                connection = MagicMock(); connection.recv.return_value=json.dumps(response).encode()+b'\n'
                with patch('broker_gate.socket.socket') as factory:
                    factory.return_value.__enter__.return_value=connection
                    self.assertEqual(BrokerGate()(),expected)
                connection.sendall.assert_called_once_with(b'{"method":"automation.status"}\n')

    def test_socket_outage_or_malformed_data_denies(self):
        with patch('broker_gate.socket.socket',side_effect=OSError('private error')):
            self.assertFalse(BrokerGate()())
        for data in (b'',b'not json\n',b'x'*4097):
            connection=MagicMock();connection.recv.return_value=data
            with patch('broker_gate.socket.socket') as factory:
                factory.return_value.__enter__.return_value=connection
                self.assertFalse(BrokerGate()())
