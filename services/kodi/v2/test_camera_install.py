import base64
import unittest
import camera_install as install

PUBLIC='ssh-ed25519 '+base64.b64encode(b'\0\0\0\x0bssh-ed25519\0\0\0\x20'+b'X'*32).decode()
class KeyTests(unittest.TestCase):
    def test_one_camera_one_source_and_only_forced_command(self):
        line=install.restricted_line(PUBLIC)
        self.assertTrue(line.startswith(b'restrict,from="192.168.1.140",command="/usr/bin/python3 /home/jelliott/.aster-camera-source/frame.py" '))
        self.assertNotIn(b'permitopen',line)
    def test_owner_keys_and_later_unrelated_keys_survive_revocation(self):
        original=b'owner-one\nowner-two\n';line=install.restricted_line(PUBLIC)
        enabled=install.keys_changed(original,line,True)
        self.assertEqual(install.keys_changed(enabled,line,False),original)
        later=enabled+b'owner-later\n'
        self.assertEqual(install.keys_changed(later,line,False),original+b'owner-later\n')
    def test_unrestricted_duplicate_and_invalid_key_denied(self):
        line=install.restricted_line(PUBLIC)
        with self.assertRaises(RuntimeError):install.keys_changed((PUBLIC+'\n').encode(),line,True)
        with self.assertRaises(RuntimeError):install.keys_changed(line+line,line,False)
        for invalid in ('ssh-rsa abc','ssh-ed25519 invalid',PUBLIC+' arbitrary-comment'):
            with self.assertRaises(RuntimeError):install.restricted_line(invalid)

if __name__=='__main__':unittest.main()
