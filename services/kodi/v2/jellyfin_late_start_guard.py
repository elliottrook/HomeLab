"""Bounded HP-only Jellyfin 2.2.0+py3 late-start repair, not an updater."""
import hashlib

BEFORE_SHA256 = 'a4532bcc3b7a3508b67b9a00cadb6523e763d9510db12dc8f1f53c74c5459112'
ANCHOR = '        self.set_item(current_file, item)\n'
GUARD = '''        # Aster: set_item can return early if playback has already ended.
        # Only report the exact item whose playback metadata was initialized.
        if self.played.get(current_file) is not item:
            return
'''


def patched_source(source):
    if hashlib.sha256(source).hexdigest() != BEFORE_SHA256:
        raise ValueError('unexpected-jellyfin-source')
    text = source.decode('utf-8')
    if text.count(ANCHOR) != 1:
        raise ValueError('unexpected-set-item-call-count')
    return text.replace(ANCHOR, ANCHOR + GUARD).encode('utf-8')
