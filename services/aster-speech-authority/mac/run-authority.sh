#!/bin/zsh
set -euo pipefail

readonly ROOT="${ASTER_SPEECH_AUTHORITY_ROOT:-${HOME}/Library/Application Support/Aster Speech Authority/current}"
readonly TTS_PORT="${ASTER_TTS_LOOPBACK_PORT:-18140}"
readonly STT_PORT="${ASTER_STT_LOOPBACK_PORT:-18141}"
readonly REMOTE_HOST="${ASTER_TUNNEL_HOST:-192.168.20.37}"
readonly REMOTE_USER="${ASTER_TUNNEL_USER:-aster-mac-speech}"
readonly SSH_KEY="${ASTER_TUNNEL_KEY:-${HOME}/Library/Application Support/Aster Speech Authority/credentials/tunnel_ed25519}"
readonly KNOWN_HOSTS="${ASTER_TUNNEL_KNOWN_HOSTS:-${HOME}/Library/AsterSpeechAuthority/known_hosts}"
readonly LOG_DIR="${HOME}/Library/Logs/Aster Speech Authority"

mkdir -p "${LOG_DIR}"
chmod 700 "${LOG_DIR}"
cd "${ROOT}"

/usr/bin/shasum -a 256 -c artifacts.sha256
python3 scripts/verify_runtime.py --root "${ROOT}"

children=()
cleanup() {
  trap - EXIT INT TERM
  for child in "${children[@]:-}"; do
    /bin/kill "${child}" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

bin/tts-server \
  --model models/qwen-talker-1.7b-base-Q8_0.gguf \
  --codec models/qwen-tokenizer-12hz-Q8_0.gguf \
  --device MTL0 --alias aster-qwen3-tts-1.7b-q8 \
  --host 127.0.0.1 --port "${TTS_PORT}" --lang English --max-batch 1 \
  >>"${LOG_DIR}/tts.log" 2>&1 &
children+=("$!")

bin/whisper-server \
  --model models/ggml-base.en.bin --host 127.0.0.1 --port "${STT_PORT}" \
  --language en --threads 4 --processors 1 --best-of 1 --beam-size 1 \
  --prompt "Aster, Home Assistant, Lutron Caseta, British Columbia, Canadian dollars, David Eby, Jason" \
  --flash-attn \
  >>"${LOG_DIR}/stt.log" 2>&1 &
children+=("$!")

python3 scripts/register_voice.py \
  --url "http://127.0.0.1:${TTS_PORT}" \
  --wav voice/aster-synthetic-reference.wav \
  --text voice/aster-synthetic-reference.txt \
  --name aster

for url in "http://127.0.0.1:${TTS_PORT}/health" "http://127.0.0.1:${STT_PORT}/health"; do
  ready=0
  for _attempt in {1..90}; do
    if /usr/bin/curl --fail --silent --max-time 2 "${url}" >/dev/null; then
      ready=1
      break
    fi
    sleep 1
  done
  if (( ! ready )); then
    print -u2 "speech authority dependency did not become healthy: ${url}"
    exit 1
  fi
done

/usr/bin/ssh -NT \
  -i "${SSH_KEY}" -o IdentitiesOnly=yes \
  -o UserKnownHostsFile="${KNOWN_HOSTS}" -o StrictHostKeyChecking=yes \
  -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  -R "127.0.0.1:${TTS_PORT}:127.0.0.1:${TTS_PORT}" \
  -R "127.0.0.1:${STT_PORT}:127.0.0.1:${STT_PORT}" \
  "${REMOTE_USER}@${REMOTE_HOST}" &
children+=("$!")

while true; do
  for child in "${children[@]}"; do
    if ! /bin/kill -0 "${child}" 2>/dev/null; then
      wait "${child}" || true
      exit 1
    fi
  done
  sleep 5
done

