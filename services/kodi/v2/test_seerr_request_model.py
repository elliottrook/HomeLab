import copy
import unittest

from seerr_request_model import candidate, propose, result


def fixture(kind='movie'):
    return {'schema': 2, 'identity': 'seerr:'+kind+':123', 'media_type': kind,
            'media_id': 123, 'title': 'Example', 'year': '2026',
            'overview': 'A bounded synthetic result.', 'poster': '/poster.jpg',
            'backdrop': '/backdrop.jpg',
            'owned': False, 'availability': 'unknown', 'request_id': None, 'request_state': 'none',
            'seasons': [1, 2, 3] if kind == 'tv' else []}


class SeerrRequestModelTests(unittest.TestCase):
    def test_movie_requires_explicit_confirmation(self):
        item = candidate(fixture())
        self.assertEqual(propose(item).state, 'confirm')
        ready = propose(item, confirmed=True)
        self.assertEqual(ready.state, 'ready')
        self.assertEqual(ready.payload['seasons'], [])
        self.assertTrue(ready.payload['confirmed'])

    def test_tv_requires_real_selected_available_seasons(self):
        item = candidate(fixture('tv'))
        for selected in ((), (0,), (4,), (1, 1), ('1',)):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                propose(item, selected, True)
        proposal = propose(item, (3, 1), True)
        self.assertEqual(proposal.payload['seasons'], [1, 3])

    def test_owned_and_existing_requests_never_propose_duplicate(self):
        owned = fixture(); owned.update(owned=True, availability='available')
        self.assertEqual(propose(candidate(owned)).state, 'unavailable')
        library = fixture(); library.update(owned=True, availability='available', request_state='available')
        self.assertIsNone(candidate(library).request_id)
        self.assertEqual(propose(candidate(library)).state, 'unavailable')
        for state in ('pending', 'approved', 'processing', 'declined', 'failed'):
            value = fixture(); value.update(request_id=45, request_state=state)
            self.assertEqual(propose(candidate(value)).state, 'status')

    def test_partial_and_blocklisted_media_are_truthful_and_blocked(self):
        partial = fixture('tv'); partial.update(owned=True, availability='partial')
        self.assertIn('Partly', propose(candidate(partial), (1,), True).message)
        blocked = fixture(); blocked['availability'] = 'blocklisted'
        self.assertEqual(propose(candidate(blocked), confirmed=True).message,
                         'Blocked in Seerr')

    def test_candidate_schema_identity_and_request_state_fail_closed(self):
        cases = []
        value = fixture(); value['unknown'] = True; cases.append(value)
        value = fixture(); value['identity'] = 'seerr:tv:123'; cases.append(value)
        value = fixture(); value['request_id'] = 1; cases.append(value)
        value = fixture(); value.update(owned=True, availability='unknown'); cases.append(value)
        value = fixture(); value['seasons'] = [2]; cases.append(value)
        value = fixture('tv'); value['seasons'] = [2, 1]; cases.append(value)
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                candidate(value)

    def test_result_must_match_exact_candidate_and_known_state(self):
        value = {'schema': 1, 'candidate_id': 'seerr:movie:123',
                 'request_id': 77, 'state': 'pending', 'duplicate': False}
        self.assertEqual(result(value, 'seerr:movie:123')['request_id'], 77)
        for change in ({'candidate_id': 'seerr:movie:124'}, {'state': 'none'},
                       {'request_id': 0}, {'duplicate': 1}):
            altered = copy.deepcopy(value); altered.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                result(altered, 'seerr:movie:123')
        for identity in (None, 123, 'seerr:movie:0', 'seerr:book:123'):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                result(value, identity)


if __name__ == '__main__':
    unittest.main()
