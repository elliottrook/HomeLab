import copy
import pathlib
import unittest

import s0_vm_corpus_worker as worker


ROOT = pathlib.Path(__file__).resolve().parent


def rows():
    result = []
    for index in range(30):
        split = 'train' if index < 20 else 'dev'
        result.append({
            'family_id': f's0-b{index // 10 + 1}-f{index % 10 + 1:02d}',
            'proposal_origin': 'ai-proposed-s0-draft',
            'request': 'Set a timer for ten minutes',
            'synthetic_context': 'A fictional explicit timer request.',
            'labels': {
                'required': ['timer'], 'optional': [],
                'prohibited': ['credential', 'destructive', 'permission_change',
                               'secret', 'shell', 'write'],
                'acceptable_statuses': ['plan'], 'sensitivity': 'public',
                'cloud': 'public-only', 'uncertainty': [], 'split': split,
            },
        })
    return result


class CorpusWorkerTest(unittest.TestCase):
    def test_bounded_comparison(self):
        engine = worker.load_engine_source(ROOT / 'routing_smoke.py')
        result = worker.compare_accepted(rows(), engine)
        self.assertEqual(result['format'], 's0-descriptive-result.v1')
        self.assertTrue(result['corpus_evaluated'])
        self.assertIsNone(result['stop_reason'])
        self.assertFalse(result['promotion_authorized'])
        for profile in result['profiles'].values():
            self.assertEqual(set(profile['engines']), set(worker.ENGINES))
            for value in profile['engines'].values():
                self.assertEqual(len(value['rows']), 10)
                self.assertEqual(value['warm_latency']['count'], 300)

    def test_rejects_wrong_shape_and_engine(self):
        engine = worker.load_engine_source(ROOT / 'routing_smoke.py')
        for changed in (rows()[:-1], copy.deepcopy(rows())):
            if len(changed) == 30:
                changed[0]['proposal_origin'] = 'synthetic-evaluator-fixture'
            with self.assertRaises(ValueError):
                worker.compare_accepted(changed, engine)
        with self.assertRaises(ValueError):
            worker.load_engine_source(ROOT / 's0_descriptive.py')


if __name__ == '__main__':
    unittest.main()
