import unittest

import full_aster_first_screen_launch as launch


class LaunchTests(unittest.TestCase):
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


if __name__=="__main__": unittest.main()
