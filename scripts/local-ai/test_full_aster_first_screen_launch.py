import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

import full_aster_first_screen_launch as launch


class LaunchTests(unittest.TestCase):
    zone = ZoneInfo("America/Vancouver")

    def epoch(self, hour, minute):
        return int(datetime(2026, 10, 27, hour, minute, tzinfo=self.zone).timestamp())

    def test_guardian_precedes_one_owner_scope_with_fixed_deadlines(self):
        token="0123456789abcdef"; owner="aster-full-screen-owner-"+token
        unit=owner+".scope"
        guardian=launch.guardian_command(token,unit,1000,1900)
        owner_command=launch.owner_command(owner,unit)
        self.assertEqual(guardian[0],"systemd-run")
        self.assertIn("--property=Restart=no",guardian)
        self.assertEqual(guardian[guardian.index("--rescue-at")+1],"1000")
        self.assertEqual(guardian[guardian.index("--hard-deadline")+1],"1900")
        self.assertIn("--scope",owner_command)
        self.assertIn("--wait",owner_command)
        self.assertEqual(owner_command[owner_command.index("--owner-unit")+1],unit)
        self.assertTrue(guardian[-1]==owner_command[-1]=="--effect-authorized")

    def test_exact_date_and_start_window_are_enforced(self):
        for started in (
            int(datetime(2026,10,26,3,10,tzinfo=self.zone).timestamp()),
            self.epoch(3,9), self.epoch(3,31),
            int(datetime(2026,10,28,3,10,tzinfo=self.zone).timestamp()),
        ):
            with self.subTest(started=started), self.assertRaises(ValueError):
                launch.window_deadlines(started)

    def test_guardian_reserve_is_real_and_protected_deadline_is_absolute(self):
        for hour,minute in ((3,10),(3,30)):
            started=self.epoch(hour,minute)
            rescue,hard=launch.window_deadlines(started)
            self.assertEqual(rescue-started,30*60)
            self.assertGreaterEqual(hard-rescue,15*60)
            self.assertLessEqual(hard,self.epoch(4,15))


if __name__=="__main__": unittest.main()
