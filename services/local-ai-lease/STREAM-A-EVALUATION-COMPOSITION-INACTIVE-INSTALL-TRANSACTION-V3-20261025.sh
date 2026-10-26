#!/bin/bash
set -Eeuo pipefail

archive=/tmp/stream-a-evaluation-composition-b21a6227-full.tar.gz
archive_sha=aaa0190099c1643224846310a468fe12ecae1bf25bd9c42638674f32621bdade
target=/usr/local/libexec/local-ai-lease/stream-a-evaluation
stamp=$(date -u +%Y%m%dT%H%M%SZ)
checkpoint=/var/lib/local-ai-lab/checkpoints/stream-a-evaluation-composition-b21a6227-$stamp
stage=$(mktemp -d /tmp/stream-a-composition-install.XXXXXX)
started=0

host_new=(
  stream_a_evaluation_live_plan.py
  stream_a_evaluation_sequence.py
  stream_a_evaluation_effect_driver.py
  stream_a_evaluation_handlers.py
  stream_a_evaluation_evidence_loader.py
  stream_a_evaluation_host_outcome.py
  stream_a_evaluation_restored_verifier.py
  stream_a_evaluation_runtime.py
)
host_all=("${host_new[@]}" stream_a_evaluation_restore_observer.py)
f6_units=(
  stream-a-evaluation-watchdog.service
  stream-a-evaluation-watchdog.timer
  stream-a-evaluation-owner-heartbeat.service
  stream-a-evaluation-owner-heartbeat.timer
  stream-a-evaluation-owner.service
)
state_paths=(
  /var/lib/local-ai-lab/stream-a-evaluation/lease.json
  /var/lib/local-ai-lab/stream-a-evaluation/lease.lock
  /var/lib/local-ai-lab/stream-a-evaluation/lease.operation.lock
  /var/lib/local-ai-lab/stream-a-evaluation/owner-intent.json
  /var/lib/local-ai-lab/stream-a-evaluation/owner-heartbeat.json
  /var/lib/local-ai-lab/stream-a-evaluation/watchdog-status.json
  /var/lib/local-ai-lab/stream-a-evaluation/restore-intent.json
  /etc/local-ai-lab/stream-a-evaluation/watchdog-identity.json
)

unit_value() {
  local kind=$1 unit=$2 value
  value=$(systemctl "$kind" "$unit" 2>/dev/null) || true
  printf '%s:%s:%s\n' "$unit" "$kind" "$value"
}

f2_snapshot() {
  local unit
  for unit in \
    f2-preflight-prepare.timer f2-preflight-final.timer \
    f2-preflight-prepare-20261026.timer f2-preflight-final-20261026.timer; do
    unit_value is-enabled "$unit"
    unit_value is-active "$unit"
    if test -f "/etc/systemd/system/$unit"; then
      sha256sum "/etc/systemd/system/$unit"
    else
      printf '%s:absent\n' "$unit"
    fi
  done
}

require_f6_inert() {
  local unit enabled active
  for unit in "${f6_units[@]}"; do
    enabled=$(systemctl is-enabled "$unit" 2>/dev/null) || true
    active=$(systemctl is-active "$unit" 2>/dev/null) || true
    test "$enabled" = disabled
    test "$active" = inactive
  done
}

require_state_absent() {
  local path
  for path in "${state_paths[@]}"; do test ! -e "$path"; done
}

require_production() {
  test "$(pct exec 104 -- systemctl is-active aster-agent.service)" = active
  test "$(pct exec 110 -- systemctl is-active aster-llama.service)" = active
  test "$(pct exec 116 -- systemctl is-active aster-speech.service)" = active
  for timer in news-aggregator-ingest.timer news-aggregator-digest.timer; do
    test "$(pct exec 114 -- systemctl is-enabled "$timer")" = enabled
    test "$(pct exec 114 -- systemctl is-active "$timer")" = active
  done
  test "$(systemctl is-active pvescheduler.service)" = active
  test "$(systemctl is-active pvestatd.service)" = active
}

require_ready_lease() {
  /usr/local/sbin/local-ai-lease status | python3 -c \
    'import json,sys; assert json.load(sys.stdin) == {"state":"ready"}'
}

require_dependency_pins() {
  local root name expected
  while read -r root name expected; do
    test "$(sha256sum "$root/$name" | cut -d' ' -f1)" = "$expected"
    test "$(stat -c '%U:%G:%a:%h:%F' "$root/$name")" = \
      'root:root:644:1:regular file'
  done <<'EOF'
/usr/local/libexec/local-ai-lease/stream-a-evaluation evaluation_lease.py 3d6e976b5fcb33a5645ec35fd0fe337ebbb57600edbbd03fe074b165e440a4d7
/usr/local/libexec/local-ai-lease/stream-a-evaluation evaluation_lease_adapter.py 2d4ff31f75dc98af9f745ca7e24310ac3627b9b36e8a29bf9a50f8debb0911f0
/usr/local/libexec/local-ai-lease/stream-a-evaluation evaluation_lease_watchdog.py 19606f6b398dd6f43a461704081e66f09e292c434f73f4aaee46327f9cc02f53
/usr/local/libexec/local-ai-lease/stream-a-evaluation stream_a_evaluation_watchdog.py c406dd4da579d4d5129b13131121b55ac1aacaa1a5125c9d481e0d7f847c9849
/usr/local/libexec/local-ai-lease/stream-a-evaluation stream_a_evaluation_admission.py 3e54f54239df4ceeeb9dfdf9166fdbd7b9bb9bb9bbd3d5119c17f1092480b686
/usr/local/libexec/local-ai-lease f2_scheduled_release_candidate.py 9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1
/usr/local/libexec/local-ai-lease pre_acquire_receipt.py 7c70b6c8097ec9b5b9d2dd6e980f59a6b15ebd8397fbf5acbced98a2e7cc2170
/usr/local/libexec/local-ai-lease retained_archive_integrity.py 11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5
/usr/local/libexec/local-ai-lease f2_preflight_fixed_wrapper.py e61b7de53a277b3af747693485f398f293853314e6ad49172c9e5cc43a1a5c34
/usr/local/libexec/local-ai-lease f2_preflight_snapshot.py 6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684
/usr/local/libexec/local-ai-lease lease_contract.py 420ce2ecc44bde3d17ad25218462618d150a4ec37c4a597067ebb45f8e2f780b
/usr/local/libexec/local-ai-lease lease_watchdog.py 3146d292dd42a6a3f305b67cccf5518e7c0585c9c6de2e195d1a00686003d1fc
/usr/local/libexec/local-ai-lease backup_receipt_adapter.py 26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f
EOF
}

rollback() {
  local rc=$?
  trap - ERR
  set +e
  if test "$started" = 1; then
    install -o root -g root -m 0644 \
      "$checkpoint/stream_a_evaluation_restore_observer.py" \
      "$target/.stream_a_evaluation_restore_observer.py.rollback.$$"
    mv -T "$target/.stream_a_evaluation_restore_observer.py.rollback.$$" \
      "$target/stream_a_evaluation_restore_observer.py"
    for name in "${host_new[@]}"; do rm -f "$target/$name"; done
    for vmid in 104 110; do
      pct exec "$vmid" -- rm -f \
        /usr/local/libexec/stream-a-evaluation-guest-outcome \
        /usr/local/libexec/stream_a_evaluation_outcome_verifier.py
    done
  fi
  rm -rf "$stage"
  printf '{"state":"rolled_back","source":"b21a6227","exit":%d,"checkpoint":"%s"}\n' \
    "$rc" "$checkpoint" >&2
  exit "$rc"
}
trap rollback ERR

test "$(sha256sum "$archive" | cut -d' ' -f1)" = "$archive_sha"
tar -xzf "$archive" -C "$stage"
src=$stage/scripts/local-ai

# Fresh prestate and rollback boundary.
for name in "${host_new[@]}"; do test ! -e "$target/$name"; done
test "$(sha256sum "$target/stream_a_evaluation_restore_observer.py" | cut -d' ' -f1)" = \
  70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3
test "$(stat -c '%U:%G:%a:%h:%F' "$target/stream_a_evaluation_restore_observer.py")" = \
  'root:root:644:1:regular file'
for vmid in 104 110; do
  pct exec "$vmid" -- test ! -e /usr/local/libexec/stream-a-evaluation-guest-outcome
  pct exec "$vmid" -- test ! -e /usr/local/libexec/stream_a_evaluation_outcome_verifier.py
done
require_f6_inert
require_state_absent
require_ready_lease
require_production
require_dependency_pins
f2_snapshot >"$stage/f2.before"

install -d -o root -g root -m 0700 "$checkpoint"
install -o root -g root -m 0600 \
  "$target/stream_a_evaluation_restore_observer.py" \
  "$checkpoint/stream_a_evaluation_restore_observer.py"
cat >"$checkpoint/manifest" <<EOF
source=b21a6227
archive_sha256=$archive_sha
observer_pre_sha256=70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3
absent_targets=12
EOF
chown root:root "$checkpoint/manifest"
chmod 0600 "$checkpoint/manifest"

test_log=$stage/tests.log
(
  cd "$stage"
  PYTHONPATH=scripts/local-ai PYTHONDONTWRITEBYTECODE=1 \
    python3 -B -m unittest discover -s scripts/local-ai \
      -p 'test_stream_a_evaluation*.py'
) >"$test_log" 2>&1
grep -Fq 'Ran 96 tests' "$test_log"
grep -Fq 'OK' "$test_log"

declare -A hashes=(
  [stream_a_evaluation_live_plan.py]=0f8d7e558bff48d6be9f86da62041ccaa20aa6b18780b738756d1118f0bf0ef2
  [stream_a_evaluation_sequence.py]=63eedd771d3cca25183e7f551b076c19d84e9c2855d9c7985e8cce445239aef1
  [stream_a_evaluation_effect_driver.py]=06318de809a22321b254713a9af9b87aecfa150c1cfd298c164fcab16d961f0e
  [stream_a_evaluation_handlers.py]=6977af891af538989de49c6cc67f13fe7d6953b68a9bd9d44bc9edadbbeed4a4
  [stream_a_evaluation_evidence_loader.py]=836f627cd2702dffd59c77b77adab2aded01805ee43553a11471cfddfeb80a01
  [stream_a_evaluation_host_outcome.py]=a9584bf01fea83129b8efb9a4c315ab66a37369ee386319f5632222618742225
  [stream_a_evaluation_restored_verifier.py]=a83de6bcdf0b275b9f238acda1a35e7518eae12f47eb220faf8f822d9a5e0d93
  [stream_a_evaluation_runtime.py]=7cda2842afa25bfca9cb47e30f433474c440ccf18123c80e7c55b54c66eb7210
  [stream_a_evaluation_restore_observer.py]=20d977681452eb89cbda7b0417de02b4caed279f234e7b568a072638bb736fb2
)
for name in "${host_all[@]}"; do
  test "$(sha256sum "$src/$name" | cut -d' ' -f1)" = "${hashes[$name]}"
done
test "$(sha256sum "$src/stream_a_evaluation_guest_outcome.py" | cut -d' ' -f1)" = \
  027183c9f10923cc4aa3053934b5f090d8e01f86aa81c9730d93abc143e6dcb9
test "$(sha256sum "$src/stream_a_evaluation_outcome_verifier.py" | cut -d' ' -f1)" = \
  9408623489d52f7923c8dcca246159bb13a7926aa0a820c765fc8f3a339b58e1

started=1
for name in "${host_all[@]}"; do
  install -o root -g root -m 0644 "$src/$name" "$target/.$name.new.$$"
  test "$(sha256sum "$target/.$name.new.$$" | cut -d' ' -f1)" = "${hashes[$name]}"
  mv -T "$target/.$name.new.$$" "$target/$name"
done

for vmid in 104 110; do
  pct push "$vmid" "$src/stream_a_evaluation_guest_outcome.py" \
    /tmp/stream-a-evaluation-guest-outcome.new
  pct push "$vmid" "$src/stream_a_evaluation_outcome_verifier.py" \
    /tmp/stream_a_evaluation_outcome_verifier.py.new
  pct exec "$vmid" -- install -o root -g root -m 0755 \
    /tmp/stream-a-evaluation-guest-outcome.new \
    /usr/local/libexec/.stream-a-evaluation-guest-outcome.new
  pct exec "$vmid" -- install -o root -g root -m 0644 \
    /tmp/stream_a_evaluation_outcome_verifier.py.new \
    /usr/local/libexec/.stream_a_evaluation_outcome_verifier.py.new
  pct exec "$vmid" -- mv -T \
    /usr/local/libexec/.stream-a-evaluation-guest-outcome.new \
    /usr/local/libexec/stream-a-evaluation-guest-outcome
  pct exec "$vmid" -- mv -T \
    /usr/local/libexec/.stream_a_evaluation_outcome_verifier.py.new \
    /usr/local/libexec/stream_a_evaluation_outcome_verifier.py
  pct exec "$vmid" -- rm -f \
    /tmp/stream-a-evaluation-guest-outcome.new \
    /tmp/stream_a_evaluation_outcome_verifier.py.new
done

for name in "${host_all[@]}"; do
  test "$(sha256sum "$target/$name" | cut -d' ' -f1)" = "${hashes[$name]}"
  test "$(stat -c '%U:%G:%a:%h:%F' "$target/$name")" = 'root:root:644:1:regular file'
done
PYTHONPATH="$target:/usr/local/libexec/local-ai-lease" PYTHONDONTWRITEBYTECODE=1 python3 -B -c \
  'import stream_a_evaluation_live_plan, stream_a_evaluation_sequence, stream_a_evaluation_effect_driver, stream_a_evaluation_handlers, stream_a_evaluation_evidence_loader, stream_a_evaluation_host_outcome, stream_a_evaluation_restored_verifier, stream_a_evaluation_runtime, stream_a_evaluation_restore_observer'

for vmid in 104 110; do
  test "$(pct exec "$vmid" -- sha256sum /usr/local/libexec/stream-a-evaluation-guest-outcome | cut -d' ' -f1)" = \
    027183c9f10923cc4aa3053934b5f090d8e01f86aa81c9730d93abc143e6dcb9
  test "$(pct exec "$vmid" -- sha256sum /usr/local/libexec/stream_a_evaluation_outcome_verifier.py | cut -d' ' -f1)" = \
    9408623489d52f7923c8dcca246159bb13a7926aa0a820c765fc8f3a339b58e1
  test "$(pct exec "$vmid" -- stat -c '%U:%G:%a:%h:%F' /usr/local/libexec/stream-a-evaluation-guest-outcome)" = \
    'root:root:755:1:regular file'
  test "$(pct exec "$vmid" -- stat -c '%U:%G:%a:%h:%F' /usr/local/libexec/stream_a_evaluation_outcome_verifier.py)" = \
    'root:root:644:1:regular file'
  output=$(pct exec "$vmid" -- env -i PATH=/usr/bin:/bin PYTHONPATH= \
    PYTHONDONTWRITEBYTECODE=1 python3 -B \
    /usr/local/libexec/stream-a-evaluation-guest-outcome)
  test "$output" = \
    '{"schema":"stream-a-evaluation-content-free-outcome-v1","state":"disabled"}'
done

require_f6_inert
require_state_absent
require_ready_lease
require_production
require_dependency_pins
f2_snapshot >"$stage/f2.after"
cmp -s "$stage/f2.before" "$stage/f2.after"

cat >"$checkpoint/install-result.json" <<EOF
{"checkpoint":"$checkpoint","guest_104":"disabled","guest_110":"disabled","host_tests":96,"installed_paths":13,"source":"b21a6227","state":"complete"}
EOF
chown root:root "$checkpoint/install-result.json"
chmod 0600 "$checkpoint/install-result.json"
trap - ERR
rm -rf "$stage"
rm -f "$archive"
printf '{"checkpoint":"%s","guest_104":"disabled","guest_110":"disabled","host_tests":96,"installed_paths":13,"source":"b21a6227","state":"complete"}\n' \
  "$checkpoint"
