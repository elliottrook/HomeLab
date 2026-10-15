import json
import unittest

from a1_ingress_policy import baseline, expected_rule, parse_chain, tagged_rules


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

    def test_tag_alone_is_not_an_approved_rule(self):
        self.assertFalse(expected_rule({"family": "inet", "table": "filter", "chain": "input", "comment": "aster-a1-exclusive-v1", "expr": []}))

    def test_exact_rule_shape_is_approved(self):
        rule = {"family": "inet", "table": "filter", "chain": "input", "comment": "aster-a1-exclusive-v1", "expr": [
            {"match": {"op": "!=", "left": {"payload": {"protocol": "ip", "field": "saddr"}}, "right": "192.168.70.10"}},
            {"match": {"op": "==", "left": {"payload": {"protocol": "tcp", "field": "dport"}}, "right": 11435}},
            {"counter": {}}, {"drop": None},
        ]}
        self.assertTrue(expected_rule(rule))

    def test_counter_stats_from_nft_list_are_approved(self):
        rule = {"family": "inet", "table": "filter", "chain": "input", "comment": "aster-a1-exclusive-v1", "expr": [
            {"match": {"op": "!=", "left": {"payload": {"protocol": "ip", "field": "saddr"}}, "right": "192.168.70.10"}},
            {"match": {"op": "==", "left": {"payload": {"protocol": "tcp", "field": "dport"}}, "right": 11435}},
            {"counter": {"packets": 0, "bytes": 0}}, {"drop": None},
        ]}
        self.assertTrue(expected_rule(rule))

    def test_reordered_drop_is_rejected(self):
        rule = {"family": "inet", "table": "filter", "chain": "input", "comment": "aster-a1-exclusive-v1", "expr": [
            {"drop": None},
            {"match": {"op": "!=", "left": {"payload": {"protocol": "ip", "field": "saddr"}}, "right": "192.168.70.10"}},
            {"match": {"op": "==", "left": {"payload": {"protocol": "tcp", "field": "dport"}}, "right": 11435}},
            {"counter": {}},
        ]}
        self.assertFalse(expected_rule(rule))
