# Aster Books private audio bridge (prototype)

This local Kodi add-on replaces the official Audiobookshelf add-on for Aster's
audio handoff. It uses a Kodi service
for a loopback-only, range-capable playback URL and a plugin for book parts and
podcast episodes. The service sends the Audiobookshelf key only in an outbound
HTTPS `Authorization` header; no upstream credential is put in a Kodi URL,
catalogue feed or log. A random capability in the `127.0.0.1` URL expires with
the service, and is reachable only from the Kodi host. The private UNIX control
socket has mode 0600. No credential is included in this repository.

Mac pilot: copy this add-on into Kodi's add-ons directory and enable it in
Kodi's add-on manager. A directory copy alone left it detected but disabled in
the disposable profile. With no `client.json`, the service stays closed and
the Aster listening action shows a clear unavailable message; this path was
checked in the Mac UI. With a dedicated key installed privately, live book
and podcast metadata resolved and Kodi opened an audiobook as AAC and a
downloaded podcast episode as MP3. Audible output, seeking, resume/progress
and the LibreELEC endpoint remain unverified. The live bridge returned 206
and the requested bytes for both media types; a synthetic upstream outage
returned a generic 502 without exposing the key.

Configuration for the Mac pilot: after an admin creates a key bound to the
limited Audiobookshelf user, run `python3 configure_client.py` in your own
interactive Terminal from this add-on directory. Paste the key at the hidden
prompt; the helper creates, but will not replace,
`special://profile/addon_data/plugin.audio.asterbooks/client.json` as a 0600
regular file under a 0700 add-on profile. Restart Kodi to load it. Do **not**
put the key in a command line, shell history, Git file, chat or Kodi setting.
The configured HTTPS route must reach the
Audiobookshelf API directly without an interactive SSO redirect. If the
existing domain redirects to a login page, stop: do not turn on plain HTTP or
change proxy/firewall exposure as a workaround. The existing HTTPS domain
returned live metadata with the dedicated key; no proxy change was needed.

The prototype reads item metadata and maps book `audioFiles[].ino` or podcast
`episodes[].audioFile.ino` to `/api/items/{id}/file/{ino}/download`. That raw
file endpoint and byte ranges are documented by Audiobookshelf's own client
and are synthetically tested here; the Mac Kodi pilot also reached real files.
No resume/progress synchronization, transcoding or multi-file autoplay is
claimed. The listener selects a part or episode in Kodi. A server error should
fail closed with a generic message, never expose a token.

Security limitations: another process running as the Kodi OS user could read
the config or private socket; this is a single-user Kodi endpoint, not an
isolation boundary against local malware. The loopback capability can appear
in Kodi's local playback history and logs (including Jellyfin's segment log)
and lasts until service restart or 12 hours; it is **not** a remote
Audiobookshelf credential. At service start the bridge makes Kodi's current
log owner-only (0600), and fails closed if it cannot. Use a dedicated, restricted
Audiobookshelf identity with only the Books and Podcasts libraries when
provisioning. Recovery: disable this add-on and remove its private config,
then revoke the dedicated key in Audiobookshelf. Do not install alongside a
configured official add-on using the same credential.
