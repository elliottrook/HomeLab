import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

import s0_vm_corpus_candidate_v2 as candidate
import s0_vm_corpus_worker as worker


ROOT = pathlib.Path(__file__).resolve().parents[2]


def fixture_rows(dev_ids):
    ids = [f's0-bsynthetic-train-{index:02d}' for index in range(20)] + list(dev_ids)
    rows = []
    for index, family_id in enumerate(ids):
        rows.append({
            'family_id': family_id,
            'proposal_origin': 'ai-proposed-s0-draft',
            'request': '[FIXTURE] Set a timer for ten minutes',
            'synthetic_context': '[FIXTURE] A fictional explicit timer request.',
            'labels': {
                'required': ['timer'], 'optional': [],
                'prohibited': ['credential', 'destructive', 'permission_change',
                               'secret', 'shell', 'write'],
                'acceptable_statuses': ['plan'], 'sensitivity': 'public',
                'cloud': 'public-only', 'uncertainty': [],
                'split': 'train' if index < 20 else 'dev',
            },
        })
    return rows


class CorpusCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = candidate.render(ROOT)
        cls.payload = json.loads(cls.files['payload-manifest.json'])

    def test_candidate_pins_reviewed_inputs_and_is_not_authorized(self):
        manifest = json.loads(self.files['candidate-manifest.json'])
        self.assertTrue(manifest['accepted_corpus_included'])
        self.assertFalse(manifest['accepted_corpus_evaluated'])
        self.assertFalse(manifest['executed'])
        self.assertEqual(manifest['status'], 'local-source-only-not-authorized')
        self.assertFalse(self.payload['evaluation_authorized'])
        self.assertEqual(set(self.payload['dataset_manifest']), set(candidate.CORPUS_FILES))
        for name, expected in candidate.CORPUS_MANIFEST.items():
            self.assertEqual(candidate.sha256(self.files['corpus/' + name]), expected)
        self.assertIn('source/validate_label_batch.py', self.files)
        self.assertEqual(
            set(self.payload['local_import_closure']),
            {'routing_smoke', 's0_descriptive', 's0_vm_corpus_worker',
             'validate_label_batch'})
        self.assertNotIn('RuntimeMaxSec=', self.files['aster-s0-corpus.service'].decode())
        self.assertIn('TimeoutStartSec=75', self.files['aster-s0-corpus.service'].decode())

    def test_import_closure_rejects_missing_sibling_dependency(self):
        module_root = ROOT / 'scripts/aster-adaptive'
        incomplete = {
            's0_descriptive.py': module_root / 's0_descriptive.py',
            's0_vm_corpus_worker.py': module_root / 's0_vm_corpus_worker.py',
            'routing_smoke.py': module_root / 'routing_smoke.py',
        }
        with self.assertRaisesRegex(ValueError, 'validate_label_batch'):
            candidate.validate_local_import_closure(incomplete, module_root)

    def test_generated_source_imports_under_guest_python_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory)
            for name in ('s0_descriptive.py', 's0_vm_corpus_worker.py',
                         'routing_smoke.py', 'validate_label_batch.py'):
                (source / name).write_bytes(self.files['source/' + name])
            code = ("import sys; sys.path.insert(0, " + repr(str(source)) + "); "
                    "import s0_descriptive, s0_vm_corpus_worker")
            completed = subprocess.run(
                [sys.executable, '-I', '-S', '-B', '-c', code],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=10, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr.decode())

    def test_generated_entry_and_result_validator_with_invented_rows(self):
        engine = worker.load_engine_source(ROOT / 'scripts/aster-adaptive/routing_smoke.py')
        value = worker.compare_accepted(
            fixture_rows(self.payload['development_family_ids']), engine)
        value.update({
            'run_id': candidate.RUN_ID,
            'payload_manifest_sha256': candidate.sha256(candidate.canonical(self.payload)),
            'dataset_manifest_sha256': self.payload['dataset_manifest_sha256'],
            'development_family_ids': self.payload['development_family_ids'],
            'runtime': {'python': 'fixture', 'system': 'fixture', 'machine': 'fixture'},
        })
        self.assertIs(candidate.validate_result(value, self.payload), value)
        changed = copy.deepcopy(value)
        changed['stop_reason'] = 'budget-exceeded'
        with self.assertRaises(ValueError):
            candidate.validate_result(changed, self.payload)

    def test_write_once_and_manifest_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / 'candidate'
            candidate.write_candidate(target, ROOT)
            for name, metadata in json.loads(
                    (target / 'candidate-manifest.json').read_text())['files'].items():
                raw = (target / name).read_bytes()
                self.assertEqual(len(raw), metadata['bytes'])
                self.assertEqual(candidate.sha256(raw), metadata['sha256'])
            with self.assertRaises(FileExistsError):
                candidate.write_candidate(target, ROOT)


if __name__ == '__main__':
    unittest.main()
