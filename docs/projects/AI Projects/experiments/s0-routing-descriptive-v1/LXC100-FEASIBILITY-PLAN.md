# LXC100 native systemd feasibility probe — approval candidate

Status: **NOT AUTHORIZED / NOT EXECUTED**. Constant fixture only, no accepted S0
data, evaluator source or model. Shared host100 runs Pi-hole and other services.
Target: existing Proxmox192.168.50.10, LXC100. No installation or guest reconfiguration.

## Evidence, risk and scope

Read-only verification2026-09-26: Python resolves to `/usr/bin/python3.13`;
Pi-hole is `running healthy`, restart count0; guest system state `running`.
Recheck immediately before any approved probe; old evidence is not a preflight pass.
Docker29.8.1/cgroupv2 and systemd257 are present. Nested namespace/seccomp/cgroup
operation is UNKNOWN. Unsupported controls must fail the attempt; no weakening.

Proposed mutation envelope: one temporary root-owned directory and constant canary
under `/var/tmp/aster-s0-feasibility-20260926`; one transient systemd unit named
`aster-s0-feasibility-20260926.service`; its DynamicUser ephemeral identity/cgroup/
namespaces; bounded non-secret output and normal system journal metadata. No edits
to existing units, Docker containers, firewall, DNS, LXC features, mounts outside
unit namespace, service identities, users or secrets. DynamicUser is transient
manager state, not permission for persistent account creation. No corpus transfer.

Worst plausible risk: namespace/seccomp failure or unexpected contention on shared
host100. No anticipated service interruption. Abort on service-health change;
stop only the probe, never restart Pi-hole/Docker to hide a regression. This is
not an approved operational change or a full evaluator launcher.

## Mandatory preflight (read-only standalone SSH commands)

```sh
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- systemctl is-system-running'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- docker inspect --format "{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}} {{.RestartCount}}" pihole'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- docker ps --format "{{.Names}} {{.Status}}"'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- cat /proc/meminfo'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- cat /proc/pressure/memory'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- systemctl show aster-s0-feasibility-20260926.service -p LoadState'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- test ! -e /var/tmp/aster-s0-feasibility-20260926'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- test ! -e /usr/aster-s0-feasibility-denied'
```

Require exact successful unit-query output `LoadState=not-found\n`, exit0 and
empty stderr. Any other value, warning or command failure aborts. Also require
running/healthy, unchanged restart count, no pre-existing probe path,
MemAvailable≥512MiB and memory PSI some avg10<1.00. If /proc/meminfo is host-wide
or cgroup headroom cannot be established, stop until actual guest memory.current
and memory.max headroom is read and shown≥256MiB. Do not infer spare capacity from
host memory alone. Capture existing container names/statuses for exact post-check.

DNS behavior: from Mac use existing Python stdlib to send a fixed DNS A query for
`example.org` to Pi-hole192.168.20.20:53, two-second timeout, twice before/after;
validate matching transaction ID, response flag and no error. Record only success/
latency, no answer addresses. This is a public synthetic query, not application
private data. Failure, unsupported socket access or missing baseline aborts.
The worker itself must not send DNS or any network traffic.

## Exact candidate payload and properties

`lxc100-fixture-payload.py.txt` is syntax-parsed locally only; SHA256:
`497ffce4be2431284dc8a03b5bc33e48ed4264199dba36e9c0925fe8252f9850`.
It attempts only fixed denied operations, reads a planted one-byte canary, emits
small constant-schema JSON, waits five seconds for parent inspection, and exits.
If fork unexpectedly succeeds its child exits immediately; parent reaps it and
reports failure. If write unexpectedly succeeds it removes only its own new
exclusive probe file and reports failure. No secret path is touched.

After approval, create only the canary directory using a standalone exact command:

```sh
/usr/bin/ssh -o BatchMode=yes -o ConnectTimeout=10 root@192.168.50.10 'pct exec 100 -- /usr/bin/python3.13 -I -S -B -c '"'"'import os; p="/var/tmp/aster-s0-feasibility-20260926"; os.mkdir(p,0o755); os.chmod(p,0o755); f=os.open(p+"/canary",os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644); os.fchmod(f,0o644); os.write(f,b"x"); os.close(f)'"'"''
```

The canary is intentionally readable absent namespace protection; verify0644 and
755 rather than interpreting an ordinary DAC denial as successful isolation.
No payload file is copied to guest; parent passes the exact constant source as one
quoted argument to `/usr/bin/python3.13 -I -S -B -c`. Shell quoting must use a proper
argument encoder and preserve the verified bytes; no interpolation/eval or user text.

Exact `systemd-run` argument vector inside `pct exec 100 --`:

```text
/usr/bin/systemd-run
--unit=aster-s0-feasibility-20260926.service
--wait
--pipe
--property=Environment=LANG=C LC_ALL=C
--property=UnsetEnvironment=PYTHONPATH PYTHONHOME PYTHONUSERBASE PYTHONSTARTUP PYTHONINSPECT PYTHONWARNINGS PYTHONBREAKPOINT PYTHONPYCACHEPREFIX LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT LD_DEBUG LD_PROFILE GLIBC_TUNABLES DYLD_INSERT_LIBRARIES DYLD_LIBRARY_PATH DYLD_FRAMEWORK_PATH DYLD_FALLBACK_LIBRARY_PATH DYLD_FALLBACK_FRAMEWORK_PATH SSH_AUTH_SOCK SSH_AGENT_PID GPG_AGENT_INFO DBUS_SESSION_BUS_ADDRESS KRB5CCNAME AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN OPENAI_API_KEY ANTHROPIC_API_KEY VAULT_TOKEN BAO_TOKEN
--property=Type=exec
--property=DynamicUser=yes
--property=NoNewPrivileges=yes
--property=CapabilityBoundingSet=
--property=PrivateNetwork=yes
--property=PrivateDevices=yes
--property=ProtectSystem=strict
--property=ProtectHome=yes
--property=InaccessiblePaths=/etc /opt /srv /var /run
--property=TemporaryFileSystem=/tmp:ro
--property=ProtectKernelTunables=yes
--property=ProtectKernelModules=yes
--property=ProtectControlGroups=yes
--property=SystemCallArchitectures=native
--property=SystemCallFilter=~@network-io @mount clone clone3 fork vfork
--property=SystemCallErrorNumber=EPERM
--property=MemoryMax=67108864
--property=MemorySwapMax=0
--property=TasksMax=1
--property=CPUQuota=10%
--property=LimitCPU=2
--property=LimitFSIZE=8192
--property=RuntimeMaxSec=15
--property=TimeoutStopSec=2
--property=KillMode=control-group
--property=UMask=0077
--property=WorkingDirectory=/
/usr/bin/python3.13
-I
-S
-B
-c
<exact hash-pinned constant payload bytes as one argument>
```

This is a fixed argument specification, not an executable substitution template.
No shell evaluates angle-bracket placeholders. No property starts with optional
`-`; parse/unknown-property/namespace setup failure aborts. PrivateNetwork alone
is insufficient; both AF_INET and AF_UNIX creation must explicitly fail. TaskMax1
and fork-filter do not establish a general execve prohibition: initial Python exec
must work. This first probe tests fork/socket/filesystem constraints only; no claim
of full adversarial syscall isolation or production run readiness follows.

## Supervision and capture requirements

Parent on Mac must spawn exactly this fixed SSH invocation, with allowlisted env,
DEVNULL stdin, close_fds and own process group. Capture both streams with selectors,
maximum combined8192bytes, max read chunk1024bytes and monotonic wall deadline20s.
No unbounded `communicate()` capture. On output/deadline/malformed JSON failure,
kill/reap that SSH process group and issue exact probe-unit stop below; killing SSH
alone is not proof remote worker stopped. No retry under a fresh unit name.
The parent wrapper now exists as a **local-fixture-only candidate** in
`s0_feasibility_supervisor.py`. Its only executor accepts fixed invented child names;
remote commands can be constructed/verified but `execute_remote` always denies.
This must receive technical review before any separate live connection is proposed.
No user flag or arbitrary command/path can activate SSH. The20s deadline detects
timeout; up to2s additional bounded reap/cleanup follows a kill.

Upon `phase=ready`, read these exact properties while its five-second window is open:

```sh
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- systemctl show aster-s0-feasibility-20260926.service -p ActiveState -p MainPID -p ControlGroup -p DynamicUser -p NoNewPrivileges -p PrivateNetwork -p ProtectSystem -p InaccessiblePaths -p SystemCallFilter -p MemoryMax -p MemorySwapMax -p TasksMax -p RuntimeMaxUSec -p KillMode'
```

Require actual property values match requested protections; capture actual returned
cgroup path only after validating it is exactly under the probe unit. Read its
memory.max=67108864, memory.swap.max=0 and pids.max=1 through a narrowly validated
read-only query. Missing/inaccessible cgroup fields or missed inspection window is
INCONCLUSIVE, never pass; do not repeat automatically. Kernel memory limit is a
cgroup ceiling, not an RSS measurement; no allocation/OOM stress in this probe.
Require exit0, both expected JSON phases, all checks true, no setup warnings,
and no unexpected output. Observation of requested settings is not proof of every
failure mode; record demonstrated denials separately from untested properties.

## Postflight, cleanup and rollback

Always repeat all service/DNS/memory health checks above, compare names/statuses,
health/restart count and guest running state. Require DNS success both times and
no introduced failed/restarting container. If any check regresses, stop only the
probe and report; no automatic production repair or restart authorized.

```sh
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- systemctl stop aster-s0-feasibility-20260926.service'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 100 -- systemctl reset-failed aster-s0-feasibility-20260926.service'
/usr/bin/ssh -o BatchMode=yes -o ConnectTimeout=10 root@192.168.50.10 'pct exec 100 -- /usr/bin/python3.13 -I -S -B -c '"'"'import os,stat; p="/var/tmp/aster-s0-feasibility-20260926"; s=os.lstat(p); assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.geteuid() and stat.S_IMODE(s.st_mode)==0o755; assert os.listdir(p)==["canary"]; f=os.open(p+"/canary",os.O_RDONLY|os.O_NOFOLLOW); t=os.fstat(f); assert stat.S_ISREG(t.st_mode) and t.st_uid==os.geteuid() and t.st_nlink==1 and stat.S_IMODE(t.st_mode)==0o644; assert os.read(f,2)==b"x"; os.close(f); os.unlink(p+"/canary"); os.rmdir(p)'"'"''
```

Before deletion verify the exact owned directory contains only the one-byte canary;
if changed/unexpected files exist, stop and inspect rather than recursive deletion.
Do not delete a pre-existing path, `/usr` content or any unrelated unit. A stop on
an already-unloaded unit is recorded as such, not failure requiring wider cleanup.
Verify MainPID0/unit unloaded, probe cgroup absent and canary directory absent.
Normal journal metadata may remain; do not purge system logs. Preserve bounded
non-secret stdout/stderr, properties, health outcomes and failure record locally.
No production rollback exists beyond stopping this single transient unit/removing
its invented canary. If cleanup cannot be verified, report it and leave execution
blocked; do not escalate scope or change guest privileges.

## Authority and remaining gate

Technical review must approve this candidate and its fixture-only bounded
supervisor before any run request is actionable. Primitive and supervisor fixture tests do not validate the exact remote flow.
The canary command sources were syntax parsed, shell/argv round-tripped and
executed only after replacing the fixed remote path with a disposable local path
containing spaces; no LXC mutation occurred. Commands are generated with shlex.join,
not nested unescaped double quotes. No evaluator/corpus transfer or run is
included. Accepted-data run will require a different fully verified launcher and
explicit approval. No installation, firewall/LXC change, guest/container lifecycle,
production service restart, model access or push.

Proposed user question, **after technical review and concrete wrapper completion**:
“Approve one fixture-only isolation probe on shared LXC100: one transient unit,
a temporary readable non-secret canary, ≤64MiB cgroup memory, ≤10% CPU, ≤15s unit
runtime/20s parent deadline, ≤8KiB output, pre/post Pi-hole and host checks, exact
cleanup, and immediate abort on any unsupported control? No accepted data, new
container, installation, firewall/LXC changes, production restart or push.”

References: official version257 [execution controls](https://raw.githubusercontent.com/systemd/systemd/v257/man/systemd.exec.xml)
and [resource controls](https://raw.githubusercontent.com/systemd/systemd/v257/man/systemd.resource-control.xml).
Property documentation is not deployment proof; nested-LXC behavior remains unknown.

## Review correction record

Review identified invalid nested quoting in the initial canary examples; both
commands above are now generated from exact argument arrays. Create explicitly
sets755/644 despite caller umask, so canary DAC does not falsely prove confinement.
Cleanup uses O_NOFOLLOW and checks owned directory/regular one-link file/content;
no recursive deletion. Exact command and payload proposal hashes are recorded in
`lxc100-supervisor-manifest.json`. No live preflight/creation/cleanup was invoked.

## Inherited environment correction — required before any live probe

The previous payload cleared its environment and only tested emptiness; that did
not establish inherited-environment control. The revised proposal fixes LANG=C
and LC_ALL=C and uses systemd UnsetEnvironment for the explicit Python, dynamic
loader and credential/agent names in the argument list above, before interpreter
startup. This is a defined denylist, not a universal loader-environment guarantee.

Payload imports os first, snapshots key names only, requires the initial set to
be a subset of: LANG, LC_ALL, PATH, USER, LOGNAME, HOME, SHELL, INVOCATION_ID,
SYSTEMD_EXEC_PID, JOURNAL_STREAM, MEMORY_PRESSURE_WATCH, MEMORY_PRESSURE_WRITE.
These are expected locale/identity/manager metadata names, not evidence that their
values are trustworthy. Only the fixed locale values are checked; no value is
printed. All keys are cleared immediately before errno/json/socket/time imports.
Any unexpected key or incorrect/missing locale emits environment-rejected and exits
without socket, fork, canary or write probes. The allowlist is reviewed in code,
not expanded automatically to fit a host. No environment key/value dump is emitted.

Python -I ignores PYTHON* startup settings; it does not establish generic loader
or environment isolation before Python begins. UnsetEnvironment is the systemd
pre-start control for the named variables. Actual unit enforcement remains untested;
post-start checks cannot retrospectively prove the loader was uncontaminated. No
execution-readiness claim follows from this local test.

Cleanup now also requires exact0755 directory and0644 regular-file modes. Changed
modes abort without deleting the canary or directory. Only local disposable tests
have exercised this; no remote cleanup or new permission changes were performed.

## Candidate collector revision — 2026-09-26

The readiness record now includes the worker PID for comparison with MainPID.
The candidate observation catalog adds bounded metadata commands, a 12-second
shared collector deadline and 4 KiB combined output limit per child command.
This revision is not live-ready: integrated lifecycle and recovery review remain
outstanding. Earlier supervisor evidence hashes describe commit `1e506bd`; use
`lxc100-candidate-manifest.json` for this revision. No live entry is enabled.

## Integrated candidate revision — final review pending

See `LXC100-INTEGRATED-CANDIDATE.md` for the exact lifecycle/recovery changes.
The run proposal adds `--quiet`; create returns filesystem identity immediately.
The integrated controller never uses the older name-only stop/reset/delete
proposals. Completed-run cleanup is receipt-guarded; interruption recovery is
read-only and requires manual review. No live adapter has been enabled.
