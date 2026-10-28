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
        self.assertEqual(candidate.count(b'Window.IsActive(1118)'), 2)
        self.assertNotIn(b'!Window.IsActive', candidate)
        self.assertEqual(candidate.count(b'<visible>'), 2)

    def test_current_source_keeps_one_grouped_visible_expression(self):
        control = (b'<control type="button" id="%s"><visible>'
               b'!String.IsEmpty(Container(500).ListItem.Label) | '
               b'!String.IsEmpty(Container(501).ListItem.Label)'
               b'</visible></control>')
        raw = (b'<window>' + control % b'300' + control % b'304' + b'</window>')
        with patch.object(subject, 'CURRENT_SOURCE', subject.sha(raw)):
            candidate = subject.render(raw)
        root = subject.ET.fromstring(candidate)
        visible = root.find(".//control[@id='300']").findall('visible')
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].text.count('Window.IsActive(1118)'), 1)
        self.assertIn('] + [', visible[0].text)

    def test_parenthesized_production_candidate_is_repaired_with_brackets(self):
        selected = ("Window.IsActive(1118) | Window.IsActive(1119) | "
                    "Window.IsActive(1120) | Control.HasFocus(501) | "
                    "Control.HasFocus(502) | Control.HasFocus(503)")
        value = "(A | B) + (" + selected + ")"
        control = ('<control type="button" id="{identity}"><visible>'
                   + value + '</visible></control>')
        raw = ('<window>' + control.format(identity=300)
               + control.format(identity=304) + '</window>').encode()
        with patch.object(subject, 'BROKEN_PRODUCTION_SOURCE', subject.sha(raw)):
            candidate = subject.render(raw)
        root = subject.ET.fromstring(candidate)
        self.assertEqual(root.find(".//control[@id='300']/visible").text,
                         '[' + 'A | B' + '] + [' + selected + ']')

    def test_deployed_two_nodes_are_collapsed(self):
        raw = (b'<window><control type="button" id="300"><visible>A</visible>'
               b'<visible>B</visible></control><control type="button" id="304">'
               b'<visible>A</visible><visible>B</visible></control></window>')
        with patch.object(subject, 'DEPLOYED_SOURCE', subject.sha(raw)):
            candidate = subject.render(raw)
        root = subject.ET.fromstring(candidate)
        for identity in ('300', '304'):
            self.assertEqual(len(root.find(".//control[@id='%s']" % identity).findall('visible')), 1)


if __name__ == '__main__':
    unittest.main()
