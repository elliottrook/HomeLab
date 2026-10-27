import unittest

from acquisition_home_launcher import LauncherError, add_hub


class AcquisitionHomeLauncherTests(unittest.TestCase):
    def test_replaces_only_the_existing_requests_destination(self):
        source = "<onclick>RunScript(script.asterseerr)</onclick><label>Requests</label>"
        result = add_hub(source)
        self.assertIn("RunScript(script.asteracquisition)", result)
        self.assertIn("<label>Requests</label>", result)
        self.assertNotIn("RunScript(script.asterseerr)", result)

    def test_refuses_missing_duplicate_or_already_transformed_source(self):
        for source in ("<window/>",
                       "RunScript(script.asterseerr) RunScript(script.asterseerr)",
                       "RunScript(script.asteracquisition)"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(LauncherError,
                                            "acquisition-home-predecessor"):
                    add_hub(source)


if __name__ == "__main__":
    unittest.main()
