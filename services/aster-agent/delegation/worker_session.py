"""One supervised bootstrap; in-memory token, no renewal or authorization cache."""
import threading
import time
from credentials import CredentialUnavailable, WorkerToken


class WorkerSession:
    def __init__(self, *, enabled=False, issuer=None, clock=time.monotonic):
        self.enabled=enabled
        self.issuer=issuer if issuer is not None else WorkerToken(enabled=enabled)
        self.clock=clock
        self._lock=threading.Lock()
        self._attempted=False
        self._token=None
        self._deadline=0

    def bootstrap(self):
        with self._lock:
            if self.enabled is not True or self._attempted:
                raise CredentialUnavailable('Session bootstrap unavailable')
            self._attempted=True
            try:
                token,deadline=self.issuer.acquire(supervised=True)
                # A full bounded turn plus reporting needs room in the lease.
                if not 200<=deadline-self.clock()<=300:
                    raise ValueError('Insufficient session lifetime')
                self._token,self._deadline=token,deadline
            except Exception as exc:
                self._token=None
                stage=exc.stage if isinstance(exc,CredentialUnavailable) else None
                raise CredentialUnavailable('Session bootstrap unconfirmed',stage=stage) from None

    def __call__(self):
        with self._lock:
            if self.enabled is not True or not self._token or self.clock()>=self._deadline:
                self._token=None
                raise CredentialUnavailable('Session unavailable; no automatic renewal')
            return self._token

    def close(self):
        with self._lock:
            self._token=None
            self._attempted=True
            self.enabled=False
