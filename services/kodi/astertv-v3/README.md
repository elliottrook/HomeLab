# AsterTV v3 Mini page pilot

This directory owns the credential-free macOS page-design pilot defined by
`docs/projects/AsterTV-v3.md` PA0–PA4. It is not a production deployment tree.

## Runtime boundary

- Kodi application: `/Users/jelliott/Applications/AsterTV-v3-Pilot/Kodi.app`
- Required release: Kodi `22.0.rc1` for Apple silicon
- Upstream artifact: `kodi-22.0-Piers_rc1-arm64.dmg`
- Published and verified SHA-256:
  `5f50e35df66fdac2eb10b2915249d6ec8230da19833f1f00068200a744341e5b`
- Signing identity: `Developer ID Application: Kodi Foundation (QR7RHK8K4X)`
- Portable data:
  `/Users/jelliott/Applications/AsterTV-v3-Pilot/Kodi.app/Contents/Resources/Kodi/portable_data`

The launcher refuses to start if the dedicated application or portable marker
is absent. Never open this application by double-clicking it: doing so omits
Kodi's `-p` switch and can direct it to the retained standard profile.

The retained Mini profile at
`/Users/jelliott/Library/Application Support/Kodi` is read-only historical
evidence and must not be copied, modified or treated as the v3 baseline.

## Source and data rules

- Source Aster-owned code and assets from the immutable v2.0.7 release archive.
- Apply v3 work as an explicit overlay; never edit the v2 archive or its
  reconciliation payload.
- Use labelled synthetic normal, empty, loading, stale and error fixtures.
- Do not provision Jellyfin, YouTube, Seerr, Audiobookshelf, Home Assistant,
  camera or Aster credentials into this pilot.
- Do not use real household state, camera images, history or account data.

## Launch

Run `./run-mini-pilot.sh` from this directory. The script opens a new Kodi
instance with `-p` only after validating the application, release, marker and
portable-data boundary. On a freshly prepared profile, run
`./activate-mini-pilot.sh` after Kodi reaches Estuary. The activation helper
first proves the live `special://home` mapping from Kodi's own log, then enables
and selects only the pilot skin through local Kodi JSON-RPC.

Never launch the application directly. Direct launch omits `-p` and is outside
the pilot boundary.

