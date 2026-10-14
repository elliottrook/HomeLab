import unittest

from truenas_observer_contract import MAC_WRAPPER, MIRROR_WRAPPER, SCHEDULE_WRAPPER, dispatch


class TrueNASObserverContractTests(unittest.TestCase):
    def test_allows_only_exact_fixed_commands(self):
        self.assertEqual(dispatch("midclt call rsynctask.query"), SCHEDULE_WRAPPER)
        self.assertEqual(dispatch("midclt call filesystem.listdir /mnt/Recovery/guests/aster-lxc110"), MIRROR_WRAPPER)
        self.assertEqual(dispatch("aster-mac-pull-summary"), MAC_WRAPPER)

    def test_rejects_alternate_paths_and_commands(self):
        for command in (
            "midclt call filesystem.listdir /mnt/Recovery/configuration/mac",
            "aster-mac-pull-summary /etc/passwd",
            "sh -c id",
            "midclt call rsynctask.query --raw",
        ):
            with self.assertRaisesRegex(ValueError, "allowlisted"):
                dispatch(command)


if __name__ == "__main__":
    unittest.main()
