import json
import unittest

from a1_ingress_policy import baseline, parse_chain, tagged_rules


EMPTY = json.dumps({"nftables": [{"metainfo": {"version": "1.1.3"}}, {"chain": {
    "family": "inet", "table": "filter", "name": "input", "handle": 1,
    "type": "filter", "hook": "input", "prio": 0, "policy": "accept"}}]})


class A1IngressPolicyTests(unittest.TestCase):
    def test_observed_empty_chain_is_approved_baseline(self):
        chain, rules = parse_chain(EMPTY)
        self.assertTrue(baseline(chain, rules))

    def test_any_preexisting_rule_is_rejected(self):
        payload = json.loads(EMPTY)
        payload["nftables"].append({"rule": {"family": "inet", "table": "filter", "chain": "input", "handle": 4, "comment": "other"}})
        chain, rules = parse_chain(json.dumps(payload))
        self.assertFalse(baseline(chain, rules))

    def test_only_our_tag_is_recoverable(self):
        payload = json.loads(EMPTY)
        payload["nftables"].append({"rule": {"family": "inet", "table": "filter", "chain": "input", "handle": 9, "comment": "aster-a1-exclusive-v1"}})
        _, rules = parse_chain(json.dumps(payload))
        self.assertEqual([rule["handle"] for rule in tagged_rules(rules)], [9])
