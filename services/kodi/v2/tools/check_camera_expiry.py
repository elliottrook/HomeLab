"""HP-only wall-clock expiry proof; requests no camera images."""
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen

def request(path, post=False):
    req = Request('http://127.0.0.1:15102' + path,
                  data=b'{}' if post else None,
                  headers={'Content-Type': 'application/json'} if post else {})
    with urlopen(req, timeout=3) as reply:
        return json.loads(reply.read(4097))

def require(ok, code):
    if not ok: raise RuntimeError(code)

def main():
    require(os.uname().nodename == 'AsterTV', 'expiry-hp-only')
    require(request('/status')['active'] is False, 'expiry-view-already-active')
    cp = Path('/storage/.aster-checkpoints') / ('aster-camera-expiry-' + str(time.time_ns()))
    cp.mkdir(mode=0o700)
    result = dict(passed=False, images_requested=0, production_changed=False)
    started = time.monotonic()
    state = request('/view/start', True)
    require(state['active'] is True and state['frames'] == 0, 'expiry-start')
    # Do not stop/restart a session whose identity may have changed. If another
    # caller uses it, fail and leave its viewer alone rather than claim ownership.
    try:
        for interval in range(1, 7):
            while time.monotonic() - started < interval * 50 + (1 if interval == 6 else 0):
                time.sleep(.5)
            state = request('/status')
            elapsed = time.monotonic() - started
            require(state['frames'] == 0 and state['failures'] == 0, 'expiry-session-used')
            if interval < 6:
                require(state['active'] is True and abs(state['seconds_remaining'] - (300 - elapsed)) < 4,
                        'expiry-session-changed')
            print(json.dumps(dict(elapsed_seconds=round(elapsed, 1), active=state['active'], frames=state['frames'])), flush=True)
        require(state['active'] is False and state['seconds_remaining'] == 0, 'expiry-not-expired')
        result.update(passed=True, elapsed_seconds=round(elapsed, 1), wall_clock_expiry=True,
                      no_background_images=True, final_inactive=True)
    finally:
        proof = cp / 'proof.json'
        proof.write_text(json.dumps(result, indent=2) + '\n'); proof.chmod(0o600)
        print(json.dumps(dict(proof=str(proof), passed=result['passed'])), flush=True)

if __name__ == '__main__': main()
