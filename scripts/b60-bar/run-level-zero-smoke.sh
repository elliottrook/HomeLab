#!/bin/sh
# Candidate for an explicitly approved attempt, not an automatic retry loop.
set -eu
trial=/opt/b60-level-zero-trial-20261010
export LD_LIBRARY_PATH="$trial/root/usr/local/lib:$trial/root/usr/lib/x86_64-linux-gnu"
# Load-only checks: these do not call Level Zero or initialize the GPU.
python3 -c 'import ctypes; ctypes.CDLL("libigdfcl.so.2"); ctypes.CDLL("libigc.so.2")'
exec timeout 20 "$trial/level-zero-smoke-diagnostic"
