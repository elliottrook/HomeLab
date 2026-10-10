import unittest

from bundle_reader import payload


class BundleReaderTests(unittest.TestCase):
    def test_file_read_is_repository_and_ref_scoped(self):
        self.assertEqual({
            "tool": "get_file_content",
            "arguments": {"owner": "jason", "repo": "homelab", "filePath": "README.md", "ref": "main"},
        }, payload("get_file_content", path="README.md", ref="main", limit=20))

    def test_rejects_traversal_and_unneeded_path(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            payload("get_file_content", path="../secret", ref="main", limit=20)
        with self.assertRaisesRegex(ValueError, "not accepted"):
            payload("get_repo", path="README.md", ref="main", limit=20)

    def test_commit_limit_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            payload("list_repo_commits", path=None, ref="main", limit=101)
