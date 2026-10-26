from datetime import datetime,timedelta,timezone
import unittest
from home_delivery_health import assess

NOW=datetime(2026,10,26,7,tzinfo=timezone.utc)
class HealthTests(unittest.TestCase):
    def setUp(self):
        stamp=NOW.isoformat();self.ha=dict(ok=True,last_success_at=stamp,last_source_at=stamp,last_sha256='a'*64)
        self.hp=dict(ok=True,received_at=stamp,source_at=stamp,sha256='a'*64,readings=63)
    def test_current_matching_receipt(self):self.assertTrue(assess(self.ha,self.hp,NOW)['ok'])
    def test_failure_stale_and_clock_skew(self):
        self.assertEqual(assess(dict(self.ha,ok=False),self.hp,NOW)['code'],'delivery-unavailable')
        for seconds in (-421,11):
            self.assertEqual(assess(self.ha,dict(self.hp,received_at=(NOW+timedelta(seconds=seconds)).isoformat()),NOW)['code'],'delivery-stale')
    def test_source_stale_mismatch_and_malformed(self):
        self.assertEqual(assess(self.ha,dict(self.hp,source_at=(NOW-timedelta(seconds=601)).isoformat()),NOW)['code'],'source-stale')
        self.assertEqual(assess(self.ha,dict(self.hp,sha256='b'*64),NOW)['code'],'generation-mismatch')
        self.assertFalse(assess(self.ha,dict(self.hp,readings=True),NOW)['ok'])

if __name__=='__main__':unittest.main()
