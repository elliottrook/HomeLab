"""Approved, fixed-item private read diagnosis. No network or retained password."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def diagnose():
    start=time.monotonic()
    result=None
    try:
        result=subprocess.run(['/usr/bin/security','find-generic-password',
            '-s','com.elliottrook.aster-codex-worker','-a','authentik-app-password','-w'],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            timeout=5,check=True,env={'PATH':'/usr/bin:/bin'})
        value=result.stdout.decode().removesuffix('\n')
        valid=1<=len(value)<=16384 and not any(c.isspace() for c in value)
        status='readable_valid_shape' if valid else 'readable_invalid_shape'
        del value
    except subprocess.TimeoutExpired:
        status='keychain_read_timeout'
    except subprocess.CalledProcessError:
        status='keychain_read_denied_or_failed'
    except UnicodeError:
        status='keychain_read_invalid_encoding'
    except Exception:
        status='keychain_read_other_failure'
    finally:
        if result is not None:result.stdout=b''
    return {'status':status,'elapsed_seconds':round(time.monotonic()-start,2),
            'credentials_printed':False,'network_calls':0,'model_calls':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    parser.add_argument('--approved-sha256');args=parser.parse_args()
    digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if not args.run:print(json.dumps({'enabled':False,'sha256':digest}))
    elif args.approved_sha256!=digest:raise SystemExit('Exact diagnostic approval required')
    else:print(json.dumps(diagnose()))
