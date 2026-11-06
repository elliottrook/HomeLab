"""Compiled public-only SA4 trust candidate; never used by runtime verifiers."""
from __future__ import annotations

import hashlib
import json
import re


HEX = re.compile(r"[0-9a-f]+")


def key_sha256(key: object) -> str:
    if (not isinstance(key, dict) or set(key) != {"kty", "n", "e"}
            or key["kty"] != "RSA" or key["e"] != 65537
            or not isinstance(key["n"], str) or not HEX.fullmatch(key["n"])
            or len(key["n"]) != 512 or key["n"].startswith("0")
            or int(key["n"], 16).bit_length() != 2048
            or int(key["n"], 16) % 2 != 1):
        raise ValueError("SA4 candidate key is not canonical RSA-2048")
    raw = (json.dumps(key, sort_keys=True, separators=(",", ":"),
                      allow_nan=False) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


PUBLIC_KEYS = {
    "owner-approval": {"e": 65537, "kty": "RSA", "n": "acbd04d56774c4c45e9fa0feca2e75423163af02aa75ee211d9d04d4890b5afd0bcb1e48cc9fe9cbc44803aafcf4415dbfc6e11a6016df0ca2fa010b0a63ef6090bc2339d1cadb682007f514e3166d980a800881cdc8a478a16c489d1567d41951fd5a904bfe6046674fecaebea4e3c414e083bdf740571478b174ed48388bb327112d73d2e91d84cdf4f0f8f9a9e25bd64b9e8cd3999a4d41f531f97cba3129a2e76398b638e49d340d1acd324663eb2da7aca97446cbc9e0e634c975e5a24a258d2ac799a3a069740cb2717be0f382cb9e458db70d8fc139694a285f4985efa0e08f994e85f6db297f2fccf358e83956eeb3ced259b6d6eeef46400c9581d7"},
    "ai-pam-grant": {"e": 65537, "kty": "RSA", "n": "d4b3f5ed6c188455790cdf431a75c1b5442395c6ff8cb03eee97c2c1a474101acaeb22200f5cc8ee48cf793a0017a8faeeb13f9f07c1db32154f69a5d1ac0fe1fd51396eee6d08c7eaddeab9e43673372287ca1724c23ff570408c5081b2f797bbbd82dc5a5c49d6cdc55ee04b4591ceadfd79313bb92010d74904a84f711ec23f5f2ed9aeb18d9f9317d52beb8662f9a330cf7f218e3d051498d526739c4be39a12268583abcb880125d8ca44425c290529797fc8e31818cbe0bea2d17f399a2afb9c5df203e60801dc0368cebea522041a18094ff411f77cd1b2865501b053fda4817858168bfe386b51e5e6bfec80fa4de296c36965729c0d125ff457b94d"},
    "independent-observer": {"e": 65537, "kty": "RSA", "n": "bc7ccaa4b7bd3131462b08916a4274edf4c59684acebb972d4a2ad35ac22016b5b3613b5c3e8c71368885e244322b0dfdb79592b9c8ac1092e5d7355afd2a71e3a39bd2865e9b5b3f524ffcb596730c7aa1b621f0eec037609c83906793919af0fdebb856b0e3ab6aacd927c65393db2ec7f98e147a765a73b84ff85950705eb3e0b92b468cb5ca0a9d83a88f52fc150de48c38bc537a53ddeda362ff0e362beda5e2668e5470d6ba73a2b8acc9fb5df38fb68d6db3007f72eb81a7ab4d0ffd8dfbc9a21cc31068a9d74442063e2147a72812252dc2e538e096eb68b675963309eb4fd8a66acec987813bc8eefe349b5cf395a484193b7d668773862fc6d7b89"},
}

SIGNER_IDS = {
    "owner-approval": "jason-owner",
    "ai-pam-grant": "aster-ai-pam",
    "independent-observer": "aster-observer",
}

EXPECTED_DIGESTS = {
    "owner-approval": "17738e78d92b3ba4fff496f4d51904b6c6dd18d4acf80b3ef2a34a27ea6de946",
    "ai-pam-grant": "f9ff0e192840dc0794e4adb65dad91a608e32e5d1d389bccbeac3612f54e9cb0",
    "independent-observer": "a8b5e876898ddcd7882a51c74d8b8388bb26160c96f87ab23dbeeecab9c0892b",
}


def validate() -> None:
    roles = ("owner-approval", "ai-pam-grant", "independent-observer")
    if (tuple(PUBLIC_KEYS) != roles or tuple(SIGNER_IDS) != roles
            or tuple(EXPECTED_DIGESTS) != roles
            or len(set(SIGNER_IDS.values())) != 3
            or any(key_sha256(PUBLIC_KEYS[role]) != EXPECTED_DIGESTS[role]
                   for role in roles)):
        raise ValueError("SA4 public trust candidate changed")


validate()

AUTHORITY_TRUST_CANDIDATE = {
    role: {EXPECTED_DIGESTS[role]: {
        "signer_id": SIGNER_IDS[role], "key": PUBLIC_KEYS[role],
    }} for role in ("owner-approval", "ai-pam-grant")
}
OBSERVER_TRUST_CANDIDATE = {
    EXPECTED_DIGESTS["independent-observer"]: {
        "observer_id": SIGNER_IDS["independent-observer"],
        "key": PUBLIC_KEYS["independent-observer"],
    }
}
SOURCE_REVIEW_STATUS = "owner-accepted-source-trust"
EFFECT_AUTHORIZED = False
AUTOMATIC_ROUTING = "off"
