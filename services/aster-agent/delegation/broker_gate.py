"""Read only the existing broker kill switch; failure always denies work.

Requires the candidate automation.status method on the existing approver socket.
No fake human actor, new groups, approval calls, positive cache or state changes.
"""
import json
import socket


class BrokerGate:
    def __init__(self, path='/run/homelab-broker/approval.sock'):
        self.path = path

    def __call__(self):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(2)
                connection.connect(self.path)
                connection.sendall(b'{"method":"automation.status"}\n')
                data = b''
                while not data.endswith(b'\n'):
                    chunk = connection.recv(1024)
                    if not chunk: return False
                    data += chunk
                    if len(data) > 4096: return False
            value = json.loads(data)
            return (isinstance(value, dict) and value.get('ok') is True and
                    value.get('result') == {'global_enabled': True} and
                    type(value['result']['global_enabled']) is bool)
        except Exception:
            return False
