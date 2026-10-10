"""Synthetic-only tests for the disposable-VM result protocol."""

import base64
import json
import unittest

import s0_vm_serial as serial


RUN = 'fixture-run-001'
MANIFEST = 'a' * 64


def result(size=0):
    return {'authorization': 'not-granted', 'fixture': True, 'padding': 'x' * size}


def framed(value=None):
    return serial.encode_result(result() if value is None else value, RUN, MANIFEST)


def lines(raw):
    return raw.rstrip(b'\n').split(b'\n')


class SerialProtocolTests(unittest.TestCase):
    def reject(self, raw, run=RUN, manifest=MANIFEST):
        with self.assertRaises(ValueError):
            serial.decode_capture(raw, run, manifest)

    def test_round_trip_with_boot_noise(self):
        capture = b'kernel boot\r\nlogin disabled\n' + framed() + b'poweroff\n'
        decoded = serial.decode_capture(capture, RUN, MANIFEST)
        self.assertEqual(decoded['result'], result())
        self.assertEqual(decoded['bytes'], len(decoded['result_bytes']))

    def test_multichunk_round_trip(self):
        decoded = serial.decode_capture(framed(result(7000)), RUN, MANIFEST)
        self.assertEqual(decoded['result']['padding'], 'x' * 7000)

    def test_capture_type_and_bound(self):
        self.reject('text')
        self.reject(b'x' * (serial.MAX_CAPTURE + 1))

    def test_expected_identity_is_strict(self):
        self.reject(framed(), 'other-run', MANIFEST)
        self.reject(framed(), RUN, 'b' * 64)
        for bad in ('', '../run', 'x' * 97):
            self.reject(framed(), bad, MANIFEST)

    def test_missing_or_duplicate_envelope(self):
        data = lines(framed())
        self.reject(b'\n'.join(data[1:]) + b'\n')
        self.reject(b'\n'.join(data[:-1]) + b'\n')
        self.reject(b'\n'.join([data[0], data[0], *data[1:]]) + b'\n')
        self.reject(framed() + data[-1] + b'\n')

    def test_unknown_and_extra_protocol_records(self):
        data = lines(framed())
        unknown = b' '.join((serial.PREFIX, b'OTHER', RUN.encode()))
        self.reject(b'\n'.join([data[0], unknown, *data[1:]]) + b'\n')
        self.reject(framed() + serial.PREFIX + b' GARBAGE\n')

    def test_chunk_reorder_duplicate_and_missing(self):
        data = lines(framed(result(7000)))
        self.reject(b'\n'.join([data[0], data[2], data[1], *data[3:]]) + b'\n')
        self.reject(b'\n'.join([data[0], data[1], data[1], *data[2:]]) + b'\n')
        self.reject(b'\n'.join([data[0], *data[2:]]) + b'\n')

    def test_bad_base64_and_chunk_size(self):
        data = lines(framed())
        fields = data[1].split(b' '); fields[-1] = b'%%%'
        self.reject(b'\n'.join([data[0], b' '.join(fields), data[-1]]) + b'\n')
        fields = data[1].split(b' '); fields[-1] = base64.b64encode(b'x')
        self.reject(b'\n'.join([data[0], b' '.join(fields), data[-1]]) + b'\n')

    def test_declared_counts_and_digest(self):
        data = lines(framed())
        begin = data[0].split(b' ')
        for index, value in ((4, b'0001'), (4, b'0'), (5, b'f' * 64), (6, b'2')):
            changed = begin.copy(); changed[index] = value
            self.reject(b'\n'.join([b' '.join(changed), *data[1:]]) + b'\n')
        end = data[-1].split(b' '); end[-1] = b'f' * 64
        self.reject(b'\n'.join([*data[:-1], b' '.join(end)]) + b'\n')

    def test_noncanonical_duplicate_and_nonfinite_json(self):
        for raw in (b'{"z":1, "a":2}', b'{"a":1,"a":2}', b'{"a":NaN}'):
            digest = __import__('hashlib').sha256(raw).hexdigest().encode()
            body = base64.b64encode(raw)
            wire = b'\n'.join((
                b' '.join((serial.PREFIX, b'BEGIN', RUN.encode(), MANIFEST.encode(),
                           str(len(raw)).encode(), digest, b'1')),
                b' '.join((serial.PREFIX, b'CHUNK', RUN.encode(), b'0', body)),
                b' '.join((serial.PREFIX, b'END', RUN.encode(), str(len(raw)).encode(), digest)), b''))
            self.reject(wire)

    def test_encoder_rejects_nonfinite_and_oversize(self):
        with self.assertRaises((ValueError, TypeError)):
            framed({'x': float('nan')})
        with self.assertRaises(ValueError):
            framed(result(serial.MAX_RESULT))

    def test_canonical_json_is_exact(self):
        value = {'z': 1, 'a': ['é', True]}
        decoded = serial.decode_capture(framed(value), RUN, MANIFEST)
        self.assertEqual(decoded['result_bytes'], json.dumps(value, sort_keys=True,
            separators=(',', ':'), ensure_ascii=True).encode())


if __name__ == '__main__':
    unittest.main()
