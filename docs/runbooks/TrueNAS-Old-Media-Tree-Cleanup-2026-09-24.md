# TrueNAS Old Media Tree Cleanup — 2026-09-24

> Jason: "I moved Jellyfin media from old file structure to its new location
> orphaning some media files ... find those files ... and generally clean up
> the file tree." Decisions: 1) delete what the library already has,
> 2) import the accidentally orphaned tracked episodes, 3) delete the
> untracked only-copies and loose downloads, 4) remove the old share, and
> delete empty datasets.

## Findings (read-only)

- **The old tree is dataset `Media/media` (`/mnt/Media/media`), 2.51 TB.**
  Jellyfin, Radarr, Sonarr, Lidarr, Prowlarr and SABnzbd all mount only
  `Media/data` now.
- **Still in use, and kept:**
  - `books/` (Calibre-Web Automated; the exited `calibre` container);
  - `audiobooks/` (Audiobookshelf);
  - the `media` SMB share, which is the network path to both.
- **Classification of the rest:** file names and sizes were compared with
  `Media/data` (current and archive libraries); title/episode matching
  strips `{tvdb-…}`/`{tmdb-…}`; results were cross-checked read-only against
  the Sonarr and Radarr APIs. The categories were:
  - identical copies, and other versions of titles or episodes already in
    the library: ~900 GB;
  - **tracked in Sonarr but missing from the library** (accidental orphans):
    36 episodes, 88 GB (*The Walking Dead: Daryl Dixon*, *Location,
    Location, Location*, *Last Week Tonight*);
  - untracked only-copies: 102 shows and films, ~1.4 TB;
  - loose downloads and leftovers: ~195 GB.
  - The per-group list was given to Jason as a CSV.

## Actions

1. **Import:** 36 files were copied to `Media/data/inbox/tv/<series>/`
   (size-checked, `root:apps` 664/775), then imported with Sonarr
   `ManualImport` in move mode.
   - `DownloadedEpisodesScan` reported "Failed to import" for every folder,
     even though the manual-import preview accepted every file.
   - Result: Daryl Dixon **19/19**, Last Week Tonight **23/23**, Location,
     Location, Location **63/85** (+14). The inbox is empty.
2. **Deleted** `movies`, `tv`, `media`, `downloads`, `music`, `Library` and
   `plex` under `/mnt/Media/media`. The dataset had no snapshots, so this is
   irreversible.
   - `Media/media` went from 2,509 GB to 52 GB (books 0.85 GB, audiobooks
     49 GB).
   - Pool available went from 1,158 GB to **3,615 GB (+2.46 TB)**.
3. **SMB share `movies`** (`/mnt/Media/media/movies`) deleted.
4. **Datasets:** audited for files, children, snapshots, container mounts
   (running and stopped), SMB/NFS shares, TrueNAS tasks and app-config
   references, then removed with TrueNAS `pool.dataset.delete`
   (non-recursive, attachment-aware).
   - **Deleted (22):**
     - `Audio`, `Audio/AudioBooks`, `Audio/Music`;
     - `Video`, `Video/Movies`, `Video/TV` (`Video` held only template
       dotfiles);
     - `Written`, `Written/Books`, `Written/office_apps`;
     - `cloud`, `cloud/nextcloud-data`;
     - `Photos/Print_Publications`, `Photos/Web_Publications`;
     - `appdata/{audiobookshelf,calibre,collabora,nextcloud,pihole,qbittorrent,vaultwarden}`;
     - `appdata/files/{new,new_s}`.
   - **Left: 11 empty `Media/configs/*` children, reported `EBUSY`**
     (`Immich/{backups,picture,thumbs,upload,video}`,
     `vaultwarden/{config,db}`, `wordpress`, `readarr`, `calibre`, `dozzle`).
     The Filebrowser app mounts `/mnt/Media/configs`, which pins its child
     datasets. They are harmless (~200 KB each) and can be deleted during a
     Filebrowser stop if wanted.
   - **Kept on purpose:** every `appdata/*` that is a container mount point,
     `appdata/files` (Filebrowser database), `homes`, `shared`,
     `Jason_Home`, `Notes`, `Nextcloud_data` and `Photos/*` with data.

## Result

`Media` pool: **3.29 TiB (3.62 TB) available**, up from 1.16 TB before this
cleanup. There is no effect on Jellyfin, whose libraries never pointed at
the old tree.

## Follow-up: remaining empty datasets and Filebrowser (same day)

- **Deleted the 11 busy `Media/configs/*` datasets** with Filebrowser stopped
  (Jason approved the stop):
  - `Immich/{backups,picture,thumbs,upload,video}`;
  - `vaultwarden/{config,db}`;
  - `wordpress`, `readarr`, `calibre`, `dozzle`.
  - All verified empty immediately before deletion.
  - Total datasets removed today: 33.
- **Filebrowser, before:** it mounted only `/mnt/Media/configs` (read-write)
  at `/mnt/media`, so it showed only app configs.
- **Filebrowser, after:** Jason chose "everything read-write" over the
  recommended option (backup and Surveillance read-only), after being shown
  that this exposes `backup` (Mac config exports, Home Assistant backups,
  family documents), `configs` (app databases including Vaultwarden's) and
  Frigate recordings through a web app.
  - The storage is now `host_path /mnt/Media` → `/mnt/media`, not read-only.
    The mount path is unchanged, so Filebrowser's settings and users still
    apply.
  - Rollback: restore `additional_storage` from
    `/tmp/fb-storage-before.json` on TrueNAS (host path `/mnt/Media/configs`).
- **Checked before starting:**
  - the app's root `permissions` init container only touches its own config
    volume (no recursive `chown` of the pool);
  - no host port is published, so Filebrowser is reachable only via the
    `authentik-filebrowser-ingress` network (Authentik).
- **Effective access** (Filebrowser runs as `apps` 568):
  - every dataset is visible;
  - write works on `data`, `media` and `configs`;
  - `backup`, `Photos`, `Notes`, `Surveillance` and `homes` are read-only by
    filesystem ownership.
  - Jason chose **not** to add write ACLs for `apps` (2026-09-24).
- **Notes:**
  - TrueNAS lists the app as **"File Browser (Deprecated)"**; it will be
    removed from the catalog. A replacement is a future decision.
  - Pool-root leftover folders, not deleted:
    - `/mnt/Media/backups` (empty skeleton folders);
    - `/mnt/Media/docker` (old Dockge compose and database; Dockge now uses
      `appdata/dockge`);
    - `/mnt/Media/plex` (old Plex home dotfiles).
  - `/mnt/Media/apps` is **in use** by Calibre-Web Automated.
