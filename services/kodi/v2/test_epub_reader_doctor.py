import hashlib
import json
from pathlib import Path
import tempfile
import types
import unittest

from epub_reader_doctor import (EXPECTED_SOURCES, assess, collect,
                                parse_mounts)


MOUNTS = '\n'.join(
    f'{source} {target} nfs4 ro,nosuid,nodev,noexec,relatime 0 0'
    for target, source in EXPECTED_SOURCES.items()) + '\n'


class Command:
    def __init__(self, enabled=True, active=True):
        self.enabled = enabled
        self.active = active

    def __call__(self, args, **_kwargs):
        value = self.enabled if args[1] == 'is-enabled' else self.active
        label = 'enabled' if args[1] == 'is-enabled' else 'active'
        raw = ((label + '\n') * 2 if value else ('disabled\n' * 2)).encode()
        return types.SimpleNamespace(stdout=raw, returncode=0)


class EpubReaderDoctorTests(unittest.TestCase):
    def fixture(self, root):
        root = Path(root)
        reader = root / 'reader'
        state = root / 'state'
        output = root / 'output'
        reader.mkdir(); state.mkdir(); (output / 'ready').mkdir(parents=True)
        bundle = b'{"kind":"synthetic"}\n'
        (reader / 'bundle.json').write_bytes(bundle)
        pin = hashlib.sha256(bundle).hexdigest()
        (state / 'activation.json').write_text(json.dumps({
            'schema': 1, 'active': True, 'bundle': str(reader),
            'bundle_sha256': pin, 'output': str(output)}))
        source = 'a' * 64
        generation = output / 'generations' / '7' / source
        generation.mkdir(parents=True)
        manifest = b'{"schema":1}\n'
        (generation / 'manifest.json').write_bytes(manifest)
        (output / 'ready' / '7.json').write_text(json.dumps({
            'schema': 1, 'book_id': 7, 'source_sha256': source,
            'generation': f'generations/7/{source}',
            'manifest_sha256': hashlib.sha256(manifest).hexdigest()}))
        mounts = root / 'mounts'
        mounts.write_text(MOUNTS)
        return reader, state, output, mounts

    def test_healthy_reader_verifies_mounts_and_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            reader, state, output, mounts = self.fixture(temporary)
            value = collect(state=state, reader=reader, output=output,
                            mounts=mounts, command=Command())
            self.assertEqual((value.state, value.ready), ('Ready', 1))

    def test_changed_generation_is_reported_without_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            reader, state, output, mounts = self.fixture(temporary)
            manifest = next((output / 'generations').rglob('manifest.json'))
            manifest.write_text('{"changed":true}\n')
            value = collect(state=state, reader=reader, output=output,
                            mounts=mounts, command=Command())
            self.assertEqual(value.state, 'Needs attention')
            self.assertIn('stale', ' '.join(value.details))

    def test_inactive_automount_fails_closed_even_with_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            reader, state, output, mounts = self.fixture(temporary)
            value = collect(state=state, reader=reader, output=output,
                            mounts=mounts, command=Command(active=False))
            self.assertEqual(value.state, 'Needs attention')
            self.assertIn('automounts', value.summary)

    def test_mount_parser_and_policy_reject_writeable_mount(self):
        rows = parse_mounts(MOUNTS.replace('ro,nosuid', 'rw,nosuid'))
        value = assess(activation_ok=True, enabled=(True, True),
                       active=(True, True), mounts=rows, ready=0, invalid=0)
        self.assertEqual(value.state, 'Needs attention')

    def test_bad_activation_preserves_calibre_fallback(self):
        value = assess(activation_ok=False, enabled=(True, True),
                       active=(True, True), mounts=parse_mounts(MOUNTS),
                       ready=0, invalid=0)
        self.assertIn('Calibre fallback', ' '.join(value.details))


if __name__ == '__main__':
    unittest.main()
