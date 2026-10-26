"""One consumed two-sentence grant. Run only on speech host; never export keys."""
from array import array
import hashlib
from io import BytesIO
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import wave
sys.path.insert(0, str(Path(__file__).resolve().parent))
from narration_frames import decode

CP = Path('/var/lib/aster-speech/aster-reader-narration-20261026')
BASE = 'http://192.168.70.14:9131'
REQUEST_ID = 'aster-reader-proof-20261026'
SENTENCES = ('Mara reached the lantern house just before the rain.',
             'From the road it had looked small, almost an afterthought beside the hill.')
FILES = ('/etc/systemd/system/aster-voice-candidate.service',
         '/etc/aster-speech/voice-candidate.env','/etc/aster-speech/vulkan-renderer.env',
         '/etc/aster-speech/batch-renderer.env',
         '/opt/aster-voice-candidate/aster_voice_candidate.py',
         '/opt/aster-voice-candidate/voice_candidate.py','/opt/aster-voice-candidate/voice_protocol.py',
         '/opt/aster-voice-candidate/kokoro_candidate.py','/opt/aster-voice-candidate/vulkan_renderer_client.py')
REVIEWED_SOURCE = {
    'aster_voice_candidate.py':'c452a7b6777567c9649606c63fc9a9304ff3a48a7cda2659e100f47a32330037',
    'voice_protocol.py':'5f391f622fa99a74c279a5c8607e2cac1b9f96c293bd0f8be564fc46dda05b6e',
    'voice_candidate.py':'221aba787c41aa4ece2925317a39ec39cd0d95f3847d4c00bd1a58c136c39940',
    'kokoro_candidate.py':'72ac96e0c73392755f4332e2775f5abd84a7e3e5390bfa4fb7f49176bc1d0b6b',
    'vulkan_renderer_client.py':'9305fdfe7603a2e5a5c07008f046bcb0159e0d4958c2bc26e4bc4300fd7008c9'}

def require(ok, code):
    if not ok: raise RuntimeError(code)
def pid():
    value = subprocess.check_output(['systemctl','show','aster-voice-candidate.service','-p','MainPID','--value'],timeout=3)
    result = int(value); require(result > 1, 'narration-service-not-running'); return result
def snapshot():
    return dict(pid=pid(), files={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in FILES})
def save(name, raw):
    fd = os.open(str(CP/name), os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
def report(name, value): save(name, (json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): raise RuntimeError('narration-redirect-refused')
def health(opener):
    with opener.open(BASE+'/health',timeout=5) as reply:
        require(reply.status == 200, 'narration-health-status')
        value = json.loads(reply.read(8193))
    require(value.get('status') == 'ok' and value.get('voice') == 'aster-bm-daniel', 'narration-canonical-voice')
    return {k:value.get(k) for k in ('status','voice','voice_model','voice_policy_version')}

def main():
    os.umask(0o077)
    require(os.uname().nodename == 'aster-speech' and len(sys.argv) == 1, 'narration-speech-host-only')
    # A second invocation cannot repeat this approval, even if the first POST
    # had an uncertain outcome. Never remove/reuse this checkpoint to retry.
    CP.mkdir(mode=0o700, exist_ok=False)
    result = dict(passed=False, production_aster_changed=False, service_changed=False,
                  sentences_requested=0, rendered_audio_exported=False, word_timestamps=False)
    sent = False; ended = False; key = None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    started = None
    try:
        before = snapshot(); report('before.json', before)
        require(all(before['files']['/opt/aster-voice-candidate/'+name] == wanted
                    for name,wanted in REVIEWED_SOURCE.items()), 'narration-reviewed-source-drift')
        identity = health(opener)
        environment = dict(part.split(b'=',1) for part in Path('/proc/'+str(before['pid'])+'/environ').read_bytes().split(b'\0') if b'=' in part)
        require(environment.get(b'ASTER_VOICE_NAME',b'bm_daniel') == b'bm_daniel' and
                environment.get(b'ASTER_VOICE_LANGUAGE',b'en-gb') == b'en-gb' and
                environment.get(b'ASTER_VOICE_SPEED',b'0.95') == b'0.95', 'narration-voice-policy')
        require(environment.get(b'ASTER_VOICE_RENDERER',b'onnx') in (b'onnx',b'vulkan'), 'narration-backend-policy')
        key = environment.get(b'ASTER_SPEECH_API_KEY', b'').decode()
        environment.clear()
        require(32 <= len(key) <= 512 and not any(c.isspace() for c in key), 'narration-local-credential-unavailable')
        body = json.dumps(dict(request_id=REQUEST_ID,text=' '.join(SENTENCES))).encode()
        request = urllib.request.Request(BASE+'/v2/tts/stream', data=body, method='POST',
                   headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        report('attempt.json', dict(request_id=REQUEST_ID, sentence_count=2, retries_permitted=False,
                                  submitted_text_sha256=hashlib.sha256(' '.join(SENTENCES).encode()).hexdigest()))
        sent = True; result['sentences_requested'] = 2; started = time.monotonic()
        first_audio = []
        with opener.open(request, timeout=25) as reply:
            require(reply.status == 200 and reply.headers.get_content_type() == 'application/vnd.aster.audio-frames', 'narration-response-type')
            pcm, units = decode(reply, REQUEST_ID, on_audio=lambda:first_audio.append(time.monotonic()))
        ended = True; key = None
        elapsed = time.monotonic()-started
        require(elapsed <= 60, 'narration-time-budget')
        samples = array('h'); samples.frombytes(pcm)
        if sys.byteorder != 'little': samples.byteswap()
        peak = max(abs(v) for v in samples); rms = math.sqrt(sum(v*v for v in samples)/len(samples))
        require(peak > 100 and rms > 10, 'narration-silent-or-invalid-audio')
        require(sum(abs(v)>=32767 for v in samples)/len(samples) < .01, 'narration-audio-clipping')
        output = BytesIO()
        with wave.open(output,'wb') as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(24000);wav.writeframes(pcm)
        raw = output.getvalue(); save('sample.wav', raw)
        require(snapshot() == before, 'narration-service-drift')
        require(health(opener) == identity, 'narration-post-health-drift')
        result.update(passed=True, canonical_voice=identity, sample_rate=24000,channels=1,sample_bits=16,
            wav_bytes=len(raw),wav_sha256=hashlib.sha256(raw).hexdigest(),
            duration_seconds=len(samples)/24000,elapsed_seconds=round(elapsed,3),
            first_complete_unit_seconds=round(first_audio[0]-started,3),
            sentences=[dict(index=u.index,start_sample=u.start_sample,frames=u.frames,duration_seconds=u.duration) for u in units],
            peak=peak,rms=round(rms,2),credentials_server_local=True,service_files_and_pid_unchanged=True,
            unit_boundaries_measured=True,completed=True)
    except Exception as error:
        import re
        code = str(error); result['code'] = code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
        result['submission_uncertain'] = sent and not ended
        if sent and not ended and key:
            try:
                cancel = urllib.request.Request(BASE+'/v2/tts/'+REQUEST_ID,method='DELETE',headers={'Authorization':'Bearer '+key})
                with opener.open(cancel,timeout=5) as reply: result['owned_cancel_acknowledged'] = reply.status == 204
            except Exception: result['owned_cancel_uncertain'] = True
    finally:
        key = None; report('proof.json', result)
        # No response headers, text, environment values, PCM or keys on stdout.
        print(json.dumps(result,sort_keys=True))

if __name__ == '__main__': main()
