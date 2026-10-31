"""Synthetic timestamps; no live schedule, backup or model qualification."""
import copy
import unittest

from backup_clock_projection import project


class BackupClockProjectionTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{'id': identity, 'enabled': True, 'schedule': {
            'hour': str(hour), 'minute': '0', 'dom': '*', 'month': '*', 'dow': '*'}}
            for identity, hour in ((1, 1), (3, 2), (2, 3))]

    def check(self, day='2026-11-01', zone='America/Los_Angeles'):
        return project(self.rows, source_zone=zone, day=day)

    def test_october31_clocks_align_but_never_authorize(self):
        result = self.check('2026-10-31')
        self.assertEqual(result['status'], 'clock-aligned-not-qualified')
        self.assertTrue(result['advisory_only'])
        self.assertFalse(result['admission_granted'])

    def test_november1_la_mirror_and_mac_are_one_hour_late_in_vancouver(self):
        result = self.check()
        self.assertEqual(result['status'], 'clock-mismatch')
        mirror, mac = result['tasks'][1:]
        self.assertEqual(mirror['possible_contract_occurrences'], ['2026-11-01T03:00:00-07:00'])
        self.assertEqual(mac['possible_contract_occurrences'], ['2026-11-01T04:00:00-07:00'])
        self.assertTrue(result['tasks'][0]['ambiguous'])
        self.assertEqual(len(result['tasks'][0]['possible_contract_occurrences']), 2)

    def test_november2_mismatch_is_not_only_an_ambiguous_hour_problem(self):
        result = self.check('2026-11-02')
        self.assertEqual(result['status'], 'clock-mismatch')
        self.assertTrue(all(not row['ambiguous'] for row in result['tasks']))
        self.assertTrue(all(not row['exact_clock_match'] for row in result['tasks']))

    def test_same_contract_timezone_would_align_without_granting_authority(self):
        result = self.check(zone='America/Vancouver')
        self.assertEqual(result['status'], 'clock-aligned-not-qualified')
        self.assertFalse(result['admission_granted'])

    def test_absent_duplicate_disabled_and_non_daily_fail_closed(self):
        original = copy.deepcopy(self.rows)
        for kind in ('absent', 'duplicate', 'disabled', 'weekly'):
            self.rows = copy.deepcopy(original)
            if kind == 'absent': self.rows.pop()
            elif kind == 'duplicate': self.rows.append(copy.deepcopy(self.rows[0]))
            elif kind == 'disabled': self.rows[0]['enabled'] = False
            else: self.rows[0]['schedule']['dow'] = '1'
            with self.subTest(kind=kind):
                self.assertEqual(self.check()['status'], 'invalid')

    def test_bad_clock_timezone_and_date_fail_closed(self):
        for value in ('25', '*', '1,2', '١'):
            self.rows[0]['schedule']['hour'] = value
            self.assertEqual(self.check()['status'], 'invalid')
        self.assertEqual(self.check(zone='Unknown/Zone')['status'], 'invalid')
        self.assertEqual(self.check(day='not-a-date')['status'], 'invalid')

    def test_no_input_mutation(self):
        original = copy.deepcopy(self.rows)
        self.check()
        self.assertEqual(self.rows, original)

    def test_nonexistent_spring_time_is_not_a_scheduled_occurrence(self):
        result = self.check(day='2026-03-08')
        mirror = result['tasks'][1]
        self.assertTrue(mirror['nonexistent'])
        self.assertEqual(mirror['possible_contract_occurrences'], [])
        self.assertEqual(result['status'], 'clock-mismatch')


if __name__ == '__main__':
    unittest.main()
