# AsterTV v3 M8 Jen iPhone acceptance — 2026-11-04

## Accepted behaviour

- Safari passkey authentication opened the private Aster Remote and reported
  the Jen client connected.
- Home left Kodi's settings dialog and opened Home.
- Touchpad right/left navigation, Back from Search and idle-player preservation
  passed.
- The direct Search launcher opened window `11127`; “space” returned a ready
  300-item result set after the integrity repair below.
- Browser microphone capture and authenticated STT transport passed. The
  default recognizer heard Jason's natural British “dark” as “don't”; “Search
  for dark” with an American pronunciation succeeded. This is an accuracy
  finding, not a microphone, browser, authentication or command-dispatch fault.

## Search integrity regression and repair

M4's installer had updated `select_dispatch.py` and its component manifest but
not `family-manifest.json`'s pin for `skin/tools/select_dispatch.py`. Search
therefore failed closed after the later integrity check, exactly as designed.
The repair updates both manifests transactionally and adds a focused regression
test. Jen checkpoint:

`/storage/.aster-checkpoints/astertv-v3-m8-jen-search-authority`

The live dispatcher itself was unchanged; only its stale family-manifest pin
was reconciled. Twelve focused tests passed and the real Search acceptance then
passed.

## British-English candidate and protected-window recovery

The candidate adds an allow-listed `en-GB-media` form profile. It retains the
same English-only `base.en` model, adds a British-media `initial_prompt`, and
uses beam size three only for that request. Default HTTP and Wyoming paths are
unchanged. The Remote is the only client that asks for the profile.

Twenty-four speech-service tests passed in LXC 116's pinned environment and
seven Remote static tests passed locally. The candidate speech module started
successfully, but the Lab Hours dispatcher stopped the service four seconds
later for the protected 23:00 workload. No attempt was made to defeat or
compete with that reservation. The exact original speech module was restored
while the service remained inactive; the Remote client was never changed.

Recovery checkpoint retained on LXC 116:

`/var/lib/aster-speech/checkpoints/astertv-v3-m8-en-gb-20261104`

On 2026-11-05 the authoritative 07:05–07:35 window check returned clear. The
dispatcher had restored the original service and exact hash. All 24 speech
tests passed again in the pinned environment, then the candidate was installed
from new checkpoints:

- LXC 116:
  `/var/lib/aster-speech/checkpoints/astertv-v3-m8-en-gb-20261105`
- LXC 104:
  `/var/lib/aster/checkpoints/astertv-v3-m8-en-gb-20261105`

The speech service returned healthy, the Aster service remained active, and
the public Remote served the candidate JavaScript hash. Jason fully reopened
the iPhone Remote and confirmed that “Search for Dark” in his natural English
accent worked. No audio or transcript was retained.
