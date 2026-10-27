"""Tests for the exact Books visibility parser correction."""

import unittest
from unittest.mock import patch

import books_visibility_followup as subject


class BooksVisibilityFollowupTests(unittest.TestCase):
    def test_mixed_expressions_are_grouped(self):
        selected = ('!Window.IsActive(1110) | Control.HasFocus(501) | '
                    'Control.HasFocus(502) | Control.HasFocus(503)')
        control = ('<control type="button" id="{identity}"><visible>'
                   '(A | B) + ' + selected + '</visible></control>')
        raw = ('<window>' + control.format(identity=300)
               + control.format(identity=304) + '</window>').encode()
        with patch.object(subject, 'PREDECESSOR', subject.sha(raw)):
            candidate = subject.render(raw)
        self.assertEqual(candidate.count(b'<visible>Window.IsActive(1118)'), 2)
        self.assertNotIn(b'!Window.IsActive', candidate)
        self.assertNotIn(b') + (', candidate)


if __name__ == '__main__':
    unittest.main()
