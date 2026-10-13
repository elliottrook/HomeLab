import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from project_document_bundle_verifier import (
    Denied,
    MAX_TOTAL_BYTES,
    canonical_json,
    reverify_document_bundle,
    verify_document_bundle,
)


BASE = "a" * 40
POLICY = "b" * 64
NOW = 1_800_000_000
NONCE = "n" * 24


class ProjectDocumentBundleVerifierTests(unittest.TestCase):
    def make_bundle(self, content=None, *, entries=None, action_updates=None):
        root = Path(tempfile.mkdtemp())
        (root / "files/docs/projects").mkdir(parents=True)
        content = {"docs/projects/example.md": "# Example\n"} if content is None else content
        for path, value in content.items():
            target = root / "files" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(value, encoding="utf-8")
        if entries is None:
            entries = [
                {"path": path, "content_sha256": hashlib.sha256(value.encode()).hexdigest(),
                 "content_size": len(value.encode())}
                for path, value in content.items()
            ]
        action = {"files": entries, "commit_message": "AI-PAM project: example"}
        if action_updates:
            action.update(action_updates)
        request = {
            "version": 1, "repository": "jason/homelab", "base_revision": BASE,
            "target_branch": "ai-pam/project-example", "nonce": NONCE,
            "issued_at": NOW - 10, "expires_at": NOW + 100,
            "policy_digest": POLICY, "signer": "cloud-producer", "action": action,
        }
        (root / "manifest.json").write_bytes(canonical_json(request))
        (root / "manifest.sig").write_bytes(b"signature")
        return root, request

    def verify(self, root, *, now=NOW):
        return verify_document_bundle(
            root, current_base_revision=BASE, policy_digest=POLICY,
            verify_signature=lambda body, signature, signer: signature == b"signature"
            and signer == "cloud-producer", now=now,
        )

    def test_accepts_sorted_multifile_text_package(self):
        root, _ = self.make_bundle({
            "docs/projects/Z.md": "z\n", "docs/handovers/a.txt": "a\n",
        })
        verified = self.verify(root)
        self.assertEqual(["docs/handovers/a.txt", "docs/projects/Z.md"],
                         [document.path for document in verified.documents])

    def test_rejects_schema_signature_base_and_policy_mismatch(self):
        root, request = self.make_bundle()
        request["unexpected"] = True
        (root / "manifest.json").write_bytes(canonical_json(request))
        with self.assertRaises(Denied):
            self.verify(root)
        root, request = self.make_bundle()
        request["base_revision"] = "c" * 40
        (root / "manifest.json").write_bytes(canonical_json(request))
        with self.assertRaises(Denied):
            self.verify(root)

    def test_rejects_paths_collisions_and_unsupported_types(self):
        for path in ("docs/projects/../secret.md", "docs/projects/.hidden.md", "README.md", "docs/projects/code.py"):
            root, _ = self.make_bundle({path: "x\n"})
            with self.assertRaises(Denied, msg=path):
                self.verify(root)
        root, _ = self.make_bundle({"docs/projects/a.md": "a\n", "docs/projects/A.md": "A\n"})
        with self.assertRaises(Denied):
            self.verify(root)

    def test_rejects_symlink_and_unexpected_package_entries(self):
        root, _ = self.make_bundle()
        (root / "files/docs/projects/link.md").symlink_to(root / "files/docs/projects/example.md")
        with self.assertRaises(Denied):
            self.verify(root)
        root, _ = self.make_bundle()
        files_target = root.parent / (root.name + "-files")
        (root / "files").rename(files_target)
        (root / "files").symlink_to(files_target, target_is_directory=True)
        with self.assertRaises(Denied):
            self.verify(root)
        root, _ = self.make_bundle()
        outer = root.parent / (root.name + "-link")
        outer.symlink_to(root, target_is_directory=True)
        with self.assertRaises(Denied):
            self.verify(outer)
        root, _ = self.make_bundle()
        (root / "extra.txt").write_text("unexpected", encoding="utf-8")
        with self.assertRaises(Denied):
            self.verify(root)

    def test_rejects_secret_private_address_and_private_hostname(self):
        for value in ("token: abc123\n", "server 192.168.70.10\n", "host app.internal\n"):
            root, _ = self.make_bundle({"docs/projects/example.md": value})
            with self.assertRaises(Denied, msg=value):
                self.verify(root)

    def test_rejects_limits_and_content_tamper(self):
        huge = "x" * (MAX_TOTAL_BYTES + 1)
        root, _ = self.make_bundle({"docs/projects/example.md": huge})
        with self.assertRaises(Denied):
            self.verify(root)
        root, _ = self.make_bundle()
        verified = self.verify(root)
        (root / "files/docs/projects/example.md").write_text("changed\n", encoding="utf-8")
        with self.assertRaises(Denied):
            reverify_document_bundle(verified, bundle_dir=root,
                                     current_base_revision=BASE,
                                     policy_digest=POLICY, now=NOW)

    def test_reverify_rechecks_base_policy_and_expiry(self):
        root, _ = self.make_bundle()
        verified = self.verify(root)
        with self.assertRaises(Denied):
            reverify_document_bundle(verified, bundle_dir=root,
                                     current_base_revision="c" * 40,
                                     policy_digest=POLICY, now=NOW)
        with self.assertRaises(Denied):
            reverify_document_bundle(verified, bundle_dir=root,
                                     current_base_revision=BASE,
                                     policy_digest="c" * 64, now=NOW)
        with self.assertRaises(Denied):
            reverify_document_bundle(verified, bundle_dir=root,
                                     current_base_revision=BASE,
                                     policy_digest=POLICY, now=NOW + 101)


if __name__ == "__main__":
    unittest.main()
