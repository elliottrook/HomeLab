# D4 incident-store custody — offline check

**State:** candidate only; no live incident route or connected Codex tool.

The proposed SQLite incident store retains diagnostic facts and hypotheses.
Its prior constructor created a directory with a requested private mode but
did not verify an existing directory or database. On a normal permissive
process umask, the SQLite database could be created readable by other local
users. A pre-existing symlink or permissive directory was also accepted.

The candidate now requires the incident directory to be owned by the running
identity and mode 0700, and the database to be a single regular, non-symlink
file owned by that identity and mode 0600. It checks custody before each
SQLite connection and fails closed rather than silently changing permissions
on an existing file. Local tests confirm private creation and rejection of a
0644 database, 0755 directory and symlinked database. The focused incident
store, stream and investigation suites passed 21/21.

This does not establish production process identity, backup/retention policy,
model-egress safety or the M1 approval boundary. Any deployment needs a
separate review of the store path and its owner, plus recovery and data
retention checks.
