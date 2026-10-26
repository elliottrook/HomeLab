from copy import deepcopy
from datetime import datetime,timedelta,timezone
import unittest
from home_freshness import assess

NOW = datetime(2026,10,25,20,tzinfo=timezone.utc)


def feed(publication_age=1,source_age=2):
    return dict(schema_version=1,snapshot=dict(schema_version=3),
        generated_at=(NOW-timedelta(seconds=publication_age)).isoformat(),
        source_updated_at=(NOW-timedelta(seconds=source_age)).isoformat())


class HomeFreshnessTests(unittest.TestCase):
    def test_both_clocks_recent_permits_separate_value_validation(self):
        status = assess(feed(),NOW)
        self.assertEqual(status.state,'fresh')
        self.assertTrue(status.permits_value_validation)
        self.assertEqual((status.publication_age,status.source_age),(1,2))

    def test_new_wrapper_does_not_revive_old_source(self):
        status = assess(feed(0,320760),NOW)
        self.assertEqual(status.state,'stale')
        self.assertFalse(status.permits_value_validation)

    def test_old_wrapper_stays_stale_even_with_newer_source(self):
        self.assertEqual(assess(feed(610,605),NOW).state,'stale')

    def test_exact_age_and_subsecond_boundary(self):
        self.assertEqual(assess(feed(0,600),NOW).state,'fresh')
        self.assertEqual(assess(feed(0,600.01),NOW).state,'stale')

    def test_future_source_or_publication_refused(self):
        for publication,source in ((-301,0),(0,-301)):
            with self.subTest(publication=publication,source=source):
                self.assertEqual(assess(feed(publication,source),NOW).state,'future')

    def test_bounded_clock_skew_tolerated_but_impossible_order_refused(self):
        self.assertEqual(assess(feed(0,-300),NOW).state,'fresh')
        self.assertEqual(assess(feed(500,100),NOW).state,'invalid')

    def test_missing_payload_or_timestamp_is_not_live(self):
        self.assertEqual(assess(None,NOW).state,'missing')
        for key in ('generated_at','source_updated_at'):
            payload=feed();del payload[key]
            self.assertEqual(assess(payload,NOW).state,'invalid')

    def test_invalid_naive_or_oversize_stamps(self):
        for stamp in ('not-a-date','2026-10-25T20:00:00','x'*81,True,0,[],None):
            for key in ('generated_at','source_updated_at'):
                payload=feed();payload[key]=stamp
                self.assertEqual(assess(payload,NOW).state,'invalid')

    def test_explicit_utc_and_timezone_offsets(self):
        payload=feed(0,0)
        payload['generated_at']='2026-10-25T20:00:00Z'
        payload['source_updated_at']='2026-10-25T13:00:00-07:00'
        self.assertEqual(assess(payload,NOW).state,'fresh')

    def test_unknown_or_boolean_schema_is_not_accepted(self):
        for payload in ({},[],True,dict(feed(),schema_version=True),
                dict(feed(),snapshot=dict(schema_version=True)),
                dict(feed(),snapshot=dict(schema_version=4))):
            self.assertEqual(assess(payload,NOW).state,'invalid')

    def test_caller_must_supply_aware_clock(self):
        for now in (None,'now',datetime(2026,10,25)):
            with self.assertRaises(ValueError):assess(feed(),now)

    def test_no_payload_mutation_retention_or_value_validation_claim(self):
        payload=feed();payload['snapshot']['lights']='deliberately not a valid value contract'
        before=deepcopy(payload)
        status=assess(payload,NOW)
        self.assertEqual(payload,before)
        self.assertTrue(status.permits_value_validation)
        self.assertEqual(set(status.__dict__),{'state','publication_age','source_age'})


if __name__=='__main__':unittest.main()
