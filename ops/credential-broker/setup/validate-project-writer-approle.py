#!/usr/bin/env python3
"""Validate the project AppRole from LXC 104 without printing secrets."""

from __future__ import annotations

import json
import ssl
import urllib.request
from urllib.error import HTTPError


ADDRESS = "https://192.168.50.24:8200/v1/"
CA_FILE = "/etc/homelab-broker/openbao-ca.crt"
CREDENTIAL_FILE = "/etc/homelab-broker/openbao-project-write-approle.json"
SECRET_PATH = "secret/data/ai-pam/forgejo-mcp-project-write"


def request(context, method, path, *, token=None, payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Vault-Token"] = token
    request = urllib.request.Request(ADDRESS + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, context=context, timeout=10) as response:
        raw = response.read()
    return json.loads(raw) if raw else {}


def main() -> None:
    with open(CREDENTIAL_FILE, encoding="utf-8") as handle:
        credential = json.load(handle)
    context = ssl.create_default_context(cafile=CA_FILE)
    login = request(context, "POST", "auth/approle/login", payload=credential)
    client_token = login["auth"]["client_token"]
    try:
        secret = request(context, "GET", SECRET_PATH, token=client_token)
        fields = sorted(secret["data"]["data"])
        if fields != ["token"]:
            raise RuntimeError("unexpected OpenBao secret fields")
        print("APPROLE_LOGIN_OK secret_fields=token")
    finally:
        try:
            request(context, "POST", "auth/token/revoke-self", token=client_token, payload={})
        except HTTPError as error:
            if error.code != 403:
                raise
            print("APPROLE_TOKEN_REVOKE_DENIED_EXPECTED ttl=5m")
        else:
            print("APPROLE_TOKEN_REVOKED")


if __name__ == "__main__":
    main()
