"""Candidate fixed-purpose custody adapters. Never invoke during discovery.

All calls require explicit enablement and separately approved provisioning.
No administrative API, arbitrary secret path, fallback credential or logging.
"""
import json
import os
import ssl
import stat
import subprocess
import time

import httpx

BAO = 'https://192.168.50.24:8200/v1/'
SECRET = 'secret/data/ai-pam/aster-worker-introspection'
POLICY = 'aster-worker-introspection-read'
TOKEN_URL = 'https://auth.elliottrook.com/application/o/token/'
KEYCHAIN_SERVICE = 'com.elliottrook.aster-codex-worker'
KEYCHAIN_ACCOUNT = 'authentik-app-password'


class CredentialUnavailable(Exception):
    def __init__(self,message,*,stage=None):
        super().__init__(message)
        self.stage=stage if stage in {'keychain_read','token_exchange','token_validation'} else None


def text_secret(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 16384 or any(c.isspace() for c in value):
        raise ValueError('Invalid credential shape')
    return value


def json_response(response):
    if response.status_code != 200:
        raise ValueError('Credential dependency unavailable')
    body = b''
    for chunk in response.iter_bytes():
        body += chunk
        if len(body) > 32768:
            raise ValueError('Credential response too large')
    value = json.loads(body)
    if not isinstance(value, dict):
        raise ValueError('Invalid credential response')
    return value


def read_approle(path):
    """Read only an explicitly supplied protected runtime credential file."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid not in (0, os.geteuid())
                or info.st_mode & 0o077 or info.st_size > 32768 or info.st_nlink != 1):
            raise ValueError('Unsafe credential file')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            value = json.loads(stream.read(32769))
        if not isinstance(value, dict) or set(value) != {'role_id', 'secret_id'}:
            raise ValueError('Invalid AppRole shape')
        return {key: text_secret(item) for key, item in value.items()}
    finally:
        os.close(fd)


class IntrospectionCredential:
    def __init__(self, approle_file, ca_file, *, enabled=False, transport=None):
        self.approle_file, self.ca_file = approle_file, ca_file
        self.enabled, self.transport = enabled, transport

    def __call__(self):
        if self.enabled is not True:
            raise CredentialUnavailable('Credential access disabled')
        try:
            identity = read_approle(self.approle_file)
            context = ssl.create_default_context(cafile=self.ca_file)
            with httpx.Client(verify=context, timeout=5, follow_redirects=False,
                              trust_env=False, transport=self.transport) as client:
                with client.stream('POST', BAO+'auth/approle/login', json=identity) as response:
                    login = json_response(response)
                token = text_secret(login['auth']['client_token'])
                try:
                    auth = login['auth']
                    if (auth.get('policies') != [POLICY] or
                            type(auth.get('lease_duration')) is not int or
                            not 0 < auth['lease_duration'] <= 300):
                        raise ValueError('Unexpected vault authority')
                    with client.stream('GET', BAO+SECRET,
                                       headers={'X-Vault-Token': token}) as response:
                        value = json_response(response)
                    credential = text_secret(value['data']['data']['client_secret'])
                finally:
                    # Failure to revoke denies delivery; short TTL bounds residual
                    # exposure when the vault disappears before revocation.
                    with client.stream('POST', BAO+'auth/token/revoke-self',
                                       headers={'X-Vault-Token': token}) as response:
                        if response.status_code not in (200, 204):
                            raise ValueError('Vault session cleanup unconfirmed')
                return credential
        except Exception:
            raise CredentialUnavailable('Gateway credential unavailable') from None


class WorkerToken:
    def __init__(self, *, enabled=False, transport=None):
        self.enabled, self.transport = enabled, transport

    def __call__(self):
        return self.acquire()[0]

    def acquire(self, *, supervised=False):
        if type(supervised) is not bool:
            raise CredentialUnavailable('Explicit credential mode required')
        if self.enabled is not True:
            raise CredentialUnavailable('Credential access disabled')
        stage='keychain_read'
        try:
            # Fixed item, no enumeration. Never place the password in argv/env.
            result = subprocess.run(['/usr/bin/security', 'find-generic-password',
                '-s', KEYCHAIN_SERVICE, '-a', KEYCHAIN_ACCOUNT, '-w'],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, timeout=90 if supervised else 5, check=True,
                env={'PATH': '/usr/bin:/bin'})
            password = text_secret(result.stdout.decode().removesuffix('\n'))
            issued_at = time.monotonic()
            stage='token_exchange'
            with httpx.Client(timeout=5, follow_redirects=False, trust_env=False,
                              transport=self.transport) as client:
                with client.stream('POST', TOKEN_URL, data={
                        'grant_type': 'client_credentials', 'client_id': 'aster-codex-worker',
                        'username': 'aster-codex-worker-mac', 'password': password,
                        'scope': 'aster.worker'}) as response:
                    value = json_response(response)
            stage='token_validation'
            if (value.get('token_type', '').lower() != 'bearer' or
                    type(value.get('expires_in')) is not int or
                    not 0 < value['expires_in'] <= 300 or
                    value.get('scope') != 'aster.worker' or value.get('refresh_token')):
                raise ValueError('Unexpected worker token')
            return text_secret(value['access_token']), issued_at + value['expires_in'] - 10
        except Exception:
            raise CredentialUnavailable('Worker credential unavailable',stage=stage) from None
