import unittest

from snapshot_contract import LibrarySnapshot, SnapshotItem, merge_snapshots, to_recommendations


class SnapshotContractTests(unittest.TestCase):
    def test_merge_is_identity_based_and_fail_closed(self):
        snapshots = [
            LibrarySnapshot("jellyfin", "now", (
                SnapshotItem("movie", "tmdb", "1", "Dune", owned=True,
                             signals=("watched",)),
            )),
            LibrarySnapshot("seerr", "now", (
                SnapshotItem("movie", "tmdb", "1", "Dune", archived=True,
                             signals=("requested",)),
                SnapshotItem("movie", "tmdb", "2", "Arrival", match_count=2),
            )),
        ]
        merged = merge_snapshots(snapshots)
        arrival, dune = merged
        self.assertTrue(dune.owned and dune.archived)
        self.assertEqual(dune.signals, ("watched", "requested"))
        self.assertEqual(to_recommendations(merged)[0].match_count, 2)
        self.assertEqual(arrival.title, "Arrival")

    def test_empty_snapshots_are_safe(self):
        self.assertEqual(merge_snapshots([]), ())
        self.assertEqual(to_recommendations(()), ())


if __name__ == "__main__":
    unittest.main()
