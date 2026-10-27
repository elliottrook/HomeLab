import hashlib
from pathlib import Path
import struct
import unittest


KODI = Path(__file__).resolve().parents[1]
SKIN = KODI / 'skin.asterhome'

# These are approved limestone launcher exports. In AsterTV they belong only in
# the navigation side rail. The Dock installer is a deliberate external app-icon
# exception retained from the owner-approved v1 deployment.
STONE = {
    'aster-icon-128.png', 'aster-icon-512.png',
    '02-home-hub.png', '04-news-digest.png',
    'home-hub-128.png', 'media-128.png', 'news-digest-128.png',
    '20-music-app.png', '21-books-app.png', '22-podcasts-app.png',
    '31-settings-app.png',
}
ALLOWED = {
    'skin.asterhome/1080i/IncludesHub.xml',
    'skin.asterhome/tools/install_macos_dock_icon.sh',
    'v2/feedback_refinements.py',
    # This bounded migration only reads the Settings launcher while inserting
    # the Requests entry into the same side-rail definition.
    'v2/review_corrections.py',
    'v2/prototype/index.html',
    'v2/script.astermusic.v2lab/resources/skins/Default/1080i/MusicLab.xml',
}

RIGHT_SIZED = {
    '07-tv.png': ((128, 128), 'e0b0937372fd09daf8cb6a39910e6f84f8651e6297bf8c950b80defba5de90a2'),
    '08-film.png': ((128, 128), 'edc27523426d94f4079926dbae872f4793d31b9b9db4ea9f37e141bb664faac9'),
    '09-archive-tv.png': ((128, 128), 'ba636f672835f826ce0c8040632cd4dd7c9af5b44360d2b6a12c6180ba67af8c'),
    '10-archive-film.png': ((128, 128), 'dec22c2d8c14800a35c418157154d1067722f8a5a085e23fb9162d5a650f851b'),
    '11-books.png': ((128, 128), 'b5cc8d0c2879a5bc6340ddd97e1336bd6d6aee5ff2c815c683909cf64b89c931'),
    '12-audiobooks.png': ((512, 512), '6506150b16216a9e961b03767ed4137508cfdb59417ffde3ee73c2efbe929256'),
    '13-music.png': ((512, 512), '7687628c861d4cd6fcfea8918df42b8af9b067ada3b41c4a8b222a1751d4ba11'),
    '19-movie-collections-128.png': ((128, 128), '397ef61365aca95e786ae226a1cf0f09991c08ad6a4c5533d413f302e15a46e4'),
    '20-music-app.png': ((128, 128), 'f1b50c435d799f04f24357e9da4965397bcbb8cef6e6ece24b98250547c8c8b8'),
    '21-books-app.png': ((128, 128), '3770edbee22e5cf6990e01dfa469270834043aba549cc04ed00f2b5c625cccd9'),
    '22-podcasts-app.png': ((128, 128), 'e6116afb4e3f1136e24696a660201c04df0de97c5bed536a3d0ae0ffd35650dc'),
    '23-music-album.png': ((128, 128), 'b2db85f26e776affe187c7480fa44687dfa61650b68bbf36536ff749955e83e2'),
    '24-music-artist.png': ((128, 128), '212503ebdcc634a84c4e60fc176745fbc42d15f9e87ff058f40e955a0da5fb98'),
    '25-music-song.png': ((128, 128), '1b9fd0a327b3adf140492703bd8eb0d10d7c676f4f49842b5ca2bf2791617bbe'),
    '26-music-playlist.png': ((128, 128), '7f09a3aa96a0dc8f88c11086ba21f209635f0d858028d6ee07caddde22290804'),
    '27-aster-media-logo.png': ((512, 341), '8ed332a41b4ce1ed3679daffef130ced492fc961ac06b4c78724225c8ef7073c'),
    '28-aster-books-logo.png': ((512, 341), 'b0024b38993899c2fe359214e7744bb8c7bd178daf53c20be59099fe1b659ed8'),
    '29-aster-music-logo.png': ((512, 341), '50c235b804ce60f0fbeb411e22e3d223675623076ed41a477d4b9c3f24ef96e2'),
    '30-aster-news-logo.png': ((512, 341), 'c9ba81d445e57ef354dc213ee2a5679f088b629910f9b9e7e3ef0063d275a6ed'),
    '31-settings-app.png': ((128, 128), 'ceeaa62bee0cef91f948d8cc3b4403743879fbc964ce64ae25dc02f7c2a6f75d'),
    # Rendered directly from the approved 33 SVG with the documented Sharp
    # recipe. The Brand Asset Library's generic 128 export has excess canvas.
    '33-aster-youtube-128.png': ((128, 128), 'b4ec6afc066fb44aae300f83b6a7e3ef9dbce8b0535695d08265fa3d03d60dda'),
    'audiobooks-128.png': ((128, 128), 'e2c155dc8dedddabf9f91dd7e760d606c6b970c8f7215abe9502cb135925c6d6'),
    'aster-compass-128.png': ((128, 128), '6b8788ade5bcc3447d93f497a296e55354e15a4dd9a403b22268c907c0f67ddf'),
    'home-hub-128.png': ((128, 128), 'ff6ed2cca1657757950ad7131be7725b3232a6c235f22cc595281c57dd1d7c74'),
    'media-128.png': ((128, 128), '28079f48e23b6c1994084a3bf5c3ac9608aa129e778a0644d0d3a2e59e4f6d01'),
    'music-128.png': ((128, 128), 'a55a09154e19e8085d034f4083f9814840b1ffeca10249830bc826afff033b37'),
    'news-digest-128.png': ((128, 128), '4ebb609603794fab07f4de21e126c5df374e517271eda530212ddbf7d6163bc1'),
}


class AssetUsageTests(unittest.TestCase):
    def test_stone_launchers_are_confined_to_side_rails(self):
        violations = []
        for path in KODI.rglob('*'):
            if (not path.is_file() or path.suffix not in ('.xml', '.py', '.html', '.sh')
                    or 'dist' in path.parts or path.name.startswith('test_')):
                continue
            relative = path.relative_to(KODI).as_posix()
            if relative in ALLOWED:
                continue
            text = path.read_text(errors='ignore')
            for asset in STONE:
                if asset in text:
                    violations.append(f'{relative}: {asset}')
        self.assertEqual(violations, [])

    def test_runtime_identity_exports_match_canonical_svg_derivatives(self):
        for name, (dimensions, expected_hash) in RIGHT_SIZED.items():
            path = SKIN / 'media' / name
            data = path.read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n', name)
            self.assertEqual(struct.unpack('!II', data[16:24]), dimensions, name)
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected_hash, name)

    def test_non_rail_podcast_surfaces_use_the_declared_placeholder(self):
        paths = (
            SKIN / '1080i/IncludesBooks.xml',
            SKIN / '1080i/custom_1120_podcasts.xml',
            SKIN / 'tools/books_data.py',
            KODI / 'plugin.audio.asterbooks/default.py',
        )
        for path in paths:
            text = path.read_text()
            self.assertIn('aster-compass-128.png', text, path.name)
            self.assertNotIn('22-podcasts-app.png', text, path.name)


if __name__ == '__main__':
    unittest.main()
