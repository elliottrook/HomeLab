"""Create an unscored response template for an independent SA3 blind review."""

from __future__ import annotations

import json
from pathlib import Path

from sa3_expanded_quality_blind_review import RUBRIC, review_packet_sha256


def build_template(packet: object) -> dict[str, object]:
    if (not isinstance(packet, dict)
            or packet.get("schema") != "aster-sa3-expanded-quality-blind-review-packet.v1"
            or packet.get("model_identity_disclosed") is not False
            or not isinstance(packet.get("cases"), list)
            or len(packet["cases"]) != 20):
        raise ValueError("invalid blind-review packet")
    identities = [row.get("id") if isinstance(row, dict) else None
                  for row in packet["cases"]]
    if any(not isinstance(ident, str) or not ident for ident in identities) \
            or len(set(identities)) != 20:
        raise ValueError("invalid blind-review identities")
    return {
        "schema": "aster-sa3-expanded-quality-blind-review.v1",
        "review_packet_sha256": review_packet_sha256(packet),
        "reviewer": "",
        "model_blind": True,
        "reviews": [
            {"id": ident, "judgments": {name: None for name in sorted(RUBRIC)}}
            for ident in identities
        ],
    }


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    args = parser.parse_args(argv)
    packet = json.loads(args.packet.read_text())
    print(json.dumps(build_template(packet), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
