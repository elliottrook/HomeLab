import datetime as dt
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('guard', Path(__file__).with_name('guest-retention-reconcile.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

class RetentionGuards(unittest.TestCase):
    def setUp(self):
        self.source = {}
        for vm in guard.ALLOWED:
            for days in range(8):
                stamp = (dt.datetime.now() - dt.timedelta(days=days)).strftime('%Y_%m_%d-%H_%M_%S')
                self.source[f'vzdump-lxc-{vm}-{stamp}.tar.zst'] = 2000000
        self.previous = {'source': self.source.copy()}

    def test_noop(self):
        self.assertEqual(guard.validate(self.source, self.source, self.previous), {})

    def test_single_pruned_file(self):
        source = self.source.copy()
        name = sorted(n for n in source if guard.guest(n) == 100)[0]
        del source[name]
        self.assertEqual(guard.validate(source, self.source, self.previous), {name:2000000})

    def test_empty_or_missing_guest(self):
        for source in [{}, {n:b for n,b in self.source.items() if guard.guest(n) != 100}]:
            with self.assertRaises(RuntimeError):
                guard.validate(source, self.source, self.previous)

    def test_retained_copy_missing_or_wrong_size(self):
        for value in [None, 1]:
            local = self.source.copy()
            name = next(iter(local))
            if value is None: del local[name]
            else: local[name] = value
            with self.assertRaises(RuntimeError):
                guard.validate(self.source, local, self.previous)

    def test_unknown_candidate(self):
        local = self.source.copy()
        local['vzdump-lxc-100-2020_01_01-00_00_00.tar.zst'] = 2000000
        with self.assertRaises(RuntimeError):
            guard.validate(self.source, local, self.previous)

    def test_deletion_spike(self):
        source = self.source.copy()
        local = self.source.copy()
        for day in range(1,27):
            local[f'vzdump-lxc-100-2020_01_{day:02d}-00_00_00.tar.zst'] = 2000000
        with self.assertRaises(RuntimeError):
            guard.validate(source, local, {'source':local})

    def test_excluded_110_preserved(self):
        local = self.source.copy()
        local['vzdump-lxc-110-2020_01_01-00_00_00.tar.zst'] = 2000000
        self.assertEqual(guard.validate(self.source, local, self.previous), {})

    def test_bootstrap_must_match_exactly(self):
        manifest = {'local_candidates':[], 'retained':[{'name':n,'bytes':b} for n,b in self.source.items()]}
        self.assertEqual(guard.validate(self.source, self.source, bootstrap=manifest), {})
        manifest['retained'].pop()
        with self.assertRaises(RuntimeError):
            guard.validate(self.source, self.source, bootstrap=manifest)

if __name__ == '__main__':
    unittest.main()
