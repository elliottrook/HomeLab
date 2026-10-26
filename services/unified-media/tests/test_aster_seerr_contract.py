import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
KODI = ROOT.parent / "kodi" / "v2"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(KODI))

from seerr_request_model import candidate as tv_candidate, propose
from aster_seerr_contract import ContractError, candidate, page, proposal, request_result


def search(kind="movie", media_id=123):
    return {"id": media_id, "mediaType": kind,
            "title": "Example", "releaseDate": "2026-04-01",
            "overview": "A bounded synthetic result.", "posterPath": "/p.jpg",
            "backdropPath": "/b.jpg"}


def detail(status=1, request=None, kind="movie"):
    return {"mediaInfo": {"status": status, "requests": [request] if request else []},
            "seasons": [{"seasonNumber": 0}, {"seasonNumber": 2}, {"seasonNumber": 1}]
            if kind == "tv" else []}


class AsterSeerrContractTests(unittest.TestCase):
    def test_wire_candidate_matches_tv_contract(self):
        value = candidate(search("tv"), detail(kind="tv"))
        parsed = tv_candidate(value)
        self.assertEqual((parsed.identity, parsed.seasons),
                         ("seerr:tv:123", (1, 2)))
        self.assertEqual(propose(parsed, (2,), True).state, "ready")

    def test_availability_and_request_states_are_truthful(self):
        available = tv_candidate(candidate(search(), detail(status=5)))
        self.assertTrue(available.owned)
        self.assertEqual((available.availability, available.request_state),
                         ("available", "available"))
        pending = tv_candidate(candidate(search(), detail(
            status=2, request={"id": 8, "status": 1})))
        self.assertEqual((pending.request_id, pending.request_state), (8, "processing"))
        blocked = tv_candidate(candidate(search(), detail(status=6)))
        self.assertEqual(propose(blocked, confirmed=True).message, "Blocked in Seerr")

    def test_page_is_query_bound_bounded_typed_and_unique(self):
        value = page("Example", "movie", [(search(), detail())])
        self.assertEqual(value["query"], "Example")
        with self.assertRaises(ContractError):
            page("Example", "tv", [(search(), detail())])
        with self.assertRaises(ContractError):
            page("Example", "all", [(search(), detail()), (search(), detail())])

    def test_proposal_is_exact_confirmed_and_season_scoped(self):
        value = {"schema": 1, "action": "request", "authority": "seerr",
                 "candidate_id": "seerr:tv:123", "media_type": "tv",
                 "media_id": 123, "seasons": [1, 2], "confirmed": True}
        self.assertEqual(proposal(value), value)
        for change in ({"confirmed": False}, {"seasons": []},
                       {"candidate_id": "seerr:movie:123"}, {"extra": True}):
            altered = dict(value); altered.update(change)
            with self.assertRaises(ContractError):
                proposal(altered)

    def test_result_contains_no_upstream_payload(self):
        value = request_result({"id": 88, "status": 1, "requestedBy": {"email": "secret"}},
                               "seerr:movie:123", duplicate=False)
        self.assertEqual(value, {"schema": 1, "candidate_id": "seerr:movie:123",
                                 "request_id": 88, "state": "pending",
                                 "duplicate": False})


if __name__ == "__main__":
    unittest.main()
