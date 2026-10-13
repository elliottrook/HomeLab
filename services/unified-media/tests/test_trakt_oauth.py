import unittest

from trakt_oauth import begin_pkce


class TraktOAuthTests(unittest.TestCase):
    def test_pkce_url_contains_state_and_challenge(self):
        state, pending = begin_pkce(
            "client-id", "https://recommendations.elliottrook.com/oauth/trakt/callback")
        self.assertTrue(state)
        self.assertTrue(pending["verifier"])
        self.assertIn("client_id=client-id", pending["url"])
        self.assertIn("code_challenge_method=S256", pending["url"])
        self.assertIn("state=" + state, pending["url"])


if __name__ == "__main__":
    unittest.main()
