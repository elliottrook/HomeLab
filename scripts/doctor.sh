#!/bin/bash

set -u

REPO="$HOME/lab/homelab"
SERVICES_CONFIG="$REPO/configs/services.conf"
BACKUP_ROOT="$HOME/lab/private-backups"
STATE_ROOT="${HOMELAB_STATE_ROOT:-$HOME/lab/monitoring-state}"

source "$REPO/scripts/lib/output.sh"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
    success "$1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

warn() {
    warning "$1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

fail() {
    error "$1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

check_tcp() {
    local display="$1"
    local ip="$2"
    local port="$3"

    if nc -z -G 3 "$ip" "$port" >/dev/null 2>&1; then
        pass "$display — $ip:$port"
    else
        fail "$display — $ip:$port"
    fi
}

check_backup_age() {
    local display="$1"
    local directory="$2"
    local maximum_hours="${3:-48}"

    if [[ ! -d "$directory" ]]; then
        warn "$display backup directory does not exist"
        return
    fi

    local latest
    latest="$(
        find "$directory" -type f ! -name '*.sha256' -print0 2>/dev/null |
        xargs -0 stat -f '%m %N' 2>/dev/null |
        sort -nr |
        head -n 1
    )"

    if [[ -z "$latest" ]]; then
        warn "$display has no backup files"
        return
    fi

    local modified_epoch
    modified_epoch="${latest%% *}"

    local now_epoch
    now_epoch="$(date +%s)"

    local age_hours
    age_hours=$(( (now_epoch - modified_epoch) / 3600 ))

    if (( age_hours <= maximum_hours )); then
        pass "$display backup is ${age_hours} hour(s) old"
    else
        warn "$display backup is ${age_hours} hour(s) old"
    fi
}

check_reported_backup() {
    local display="$1"
    local task="$2"
    local maximum_hours="${3:-30}"
    local state_file="$STATE_ROOT/backups/$task.state"

    if [[ ! -f "$state_file" ]]; then
        warn "$display has not reported monitoring status yet"
        return
    fi

    local result
    local reported_epoch
    result="$(awk -F'=' '$1 == "result" {print $2; exit}' "$state_file")"
    reported_epoch="$(awk -F'=' '$1 == "reported_epoch" {print $2; exit}' "$state_file")"

    if [[ "$result" != "success" && "$result" != "failure" ]] ||
       [[ ! "$reported_epoch" =~ ^[0-9]+$ ]]; then
        warn "$display monitoring status is invalid"
        return
    fi

    local now_epoch
    local age_seconds
    local age_hours
    now_epoch="$(date +%s)"
    age_seconds=$((now_epoch - reported_epoch))

    if (( age_seconds < 0 )); then
        warn "$display monitoring timestamp is ahead of the Mac clock"
        return
    fi

    age_hours=$((age_seconds / 3600))

    if [[ "$result" == "failure" ]]; then
        fail "$display reported a failure ${age_hours} hour(s) ago"
    elif (( age_hours > maximum_hours )); then
        warn "$display last reported success ${age_hours} hour(s) ago"
    else
        pass "$display reported verified success ${age_hours} hour(s) ago"
    fi
}

check_proxmox_guest_backup_age() {
    local display="$1"
    local vmid="$2"
    local maximum_hours="${3:-30}"
    local guest_type="${4:-qemu}"
    local archive_pattern
    local latest_epoch

    case "$guest_type" in
        qemu) archive_pattern="vzdump-qemu-${vmid}-*.vma.zst" ;;
        lxc) archive_pattern="vzdump-lxc-${vmid}-*.tar.zst" ;;
        *)
            warn "Unable to check $display backup age: unsupported guest type $guest_type"
            return
            ;;
    esac

    if ! latest_epoch="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 proxmox \
            "find /mnt/backups/dump -maxdepth 1 -type f -name '$archive_pattern' -printf '%T@\\n' 2>/dev/null | sort -nr | head -n 1"
    )"; then
        warn "Unable to check $display backup age"
        return
    fi

    latest_epoch="${latest_epoch%%.*}"

    if [[ ! "$latest_epoch" =~ ^[0-9]+$ ]]; then
        fail "$display has no Proxmox backup archive"
        return
    fi

    local now_epoch
    local age_seconds
    local age_hours
    now_epoch="$(date +%s)"
    age_seconds=$((now_epoch - latest_epoch))

    if (( age_seconds < 0 )); then
        warn "$display backup timestamp is ahead of the Mac clock"
        return
    fi

    age_hours=$((age_seconds / 3600))

    if (( age_hours <= maximum_hours )); then
        pass "$display Proxmox backup is ${age_hours} hour(s) old"
    else
        fail "$display Proxmox backup is ${age_hours} hour(s) old"
    fi
}

check_hermes() {
    local state

    if ! state="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 proxmox '
            dashboard="$(pct exec 104 -- systemctl is-active hermes-dashboard.service 2>/dev/null || true)"
            gateway="$(pct exec 104 -- runuser -u hermes -- env XDG_RUNTIME_DIR=/run/user/1000 systemctl --user is-active hermes-gateway.service 2>/dev/null || true)"
            printf "dashboard=%s\\ngateway=%s\\n" "$dashboard" "$gateway"
        '
    )"; then
        warn "Unable to check Hermes services"
        return
    fi

    if grep -qx 'dashboard=active' <<< "$state" &&
       grep -qx 'gateway=active' <<< "$state"; then
        pass "Hermes dashboard and gateway services healthy"
    else
        fail "Hermes service unhealthy: $(tr '\n' ' ' <<< "$state" | sed 's/[[:space:]]*$//')"
    fi
}

check_pihole_dns() {
    local display="$1"
    local ip="$2"
    local public_answer
    local local_answer
    local blocked_answer

    public_answer="$(dig +time=3 +tries=1 +short @"$ip" example.com A 2>/dev/null)"
    local_answer="$(dig +time=3 +tries=1 +short @"$ip" home.internal A 2>/dev/null)"
    blocked_answer="$(dig +time=3 +tries=1 +short @"$ip" doubleclick.net A 2>/dev/null)"

    if [[ -z "$public_answer" ]]; then
        fail "$display did not resolve a public domain"
    elif ! grep -qx '192\.168\.20\.20' <<< "$local_answer"; then
        fail "$display did not resolve home.internal correctly"
    elif [[ -n "$blocked_answer" ]] && ! grep -Eqx '0\.0\.0\.0|::' <<< "$blocked_answer"; then
        fail "$display did not block the test domain"
    else
        pass "$display resolves public/local DNS and blocks the test domain"
    fi
}

check_opnsense_wan() {
    local state_file="$STATE_ROOT/opnsense-wan.state"
    local wan_output
    local status=""
    local link_down=""
    local local_faults=""
    local remote_faults=""
    local crc_errs=""
    local good_pkts_rcvd=""
    local rx_missed_packets=""
    local xoff_txd=""
    local link_irq=""

    if ! wan_output="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 opnsense /bin/sh -s <<'REMOTE'
printf 'status=%s\n' "$(ifconfig ix1 | awk '/status:/{print $2; exit}')"
printf 'link_down=%s\n' "$(dmesg | grep -c 'ix1: link state changed to DOWN' || true)"
for counter in local_faults remote_faults crc_errs good_pkts_rcvd rx_missed_packets xoff_txd; do
    printf '%s=%s\n' "$counter" "$(sysctl -n "dev.ix.1.mac_stats.$counter")"
done
printf 'link_irq=%s\n' "$(sysctl -n dev.ix.1.link_irq)"
REMOTE
    )"; then
        warn "Unable to collect OPNsense WAN counters"
        return
    fi

    while IFS='=' read -r key value; do
        case "$key" in
            status) status="$value" ;;
            link_down) link_down="$value" ;;
            local_faults) local_faults="$value" ;;
            remote_faults) remote_faults="$value" ;;
            crc_errs) crc_errs="$value" ;;
            good_pkts_rcvd) good_pkts_rcvd="$value" ;;
            rx_missed_packets) rx_missed_packets="$value" ;;
            xoff_txd) xoff_txd="$value" ;;
            link_irq) link_irq="$value" ;;
        esac
    done <<< "$wan_output"

    local value
    for value in "$link_down" "$local_faults" "$remote_faults" "$crc_errs" \
        "$good_pkts_rcvd" "$rx_missed_packets" "$xoff_txd" "$link_irq"; do
        if [[ ! "$value" =~ ^[0-9]+$ ]]; then
            warn "OPNsense WAN counter output was incomplete"
            return
        fi
    done

    if [[ "$status" != "active" ]]; then
        fail "OPNsense WAN interface ix1 is $status"
        return
    fi

    mkdir -p "$STATE_ROOT"

    if [[ ! -f "$state_file" ]]; then
        {
            printf 'link_down=%s\n' "$link_down"
            printf 'local_faults=%s\n' "$local_faults"
            printf 'remote_faults=%s\n' "$remote_faults"
            printf 'crc_errs=%s\n' "$crc_errs"
            printf 'good_pkts_rcvd=%s\n' "$good_pkts_rcvd"
            printf 'rx_missed_packets=%s\n' "$rx_missed_packets"
            printf 'xoff_txd=%s\n' "$xoff_txd"
            printf 'link_irq=%s\n' "$link_irq"
        } > "$state_file"
        pass "OPNsense WAN is active; counter baseline recorded"
        return
    fi

    local prev_link_down=""
    local prev_local_faults=""
    local prev_remote_faults=""
    local prev_crc_errs=""
    local prev_good_pkts_rcvd=""
    local prev_rx_missed_packets=""
    local prev_xoff_txd=""
    local prev_link_irq=""

    while IFS='=' read -r key value; do
        case "$key" in
            link_down) prev_link_down="$value" ;;
            local_faults) prev_local_faults="$value" ;;
            remote_faults) prev_remote_faults="$value" ;;
            crc_errs) prev_crc_errs="$value" ;;
            good_pkts_rcvd) prev_good_pkts_rcvd="$value" ;;
            rx_missed_packets) prev_rx_missed_packets="$value" ;;
            xoff_txd) prev_xoff_txd="$value" ;;
            link_irq) prev_link_irq="$value" ;;
        esac
    done < "$state_file"

    for value in "$prev_link_down" "$prev_local_faults" "$prev_remote_faults" \
        "$prev_crc_errs" "$prev_good_pkts_rcvd" "$prev_rx_missed_packets" \
        "$prev_xoff_txd" "$prev_link_irq"; do
        if [[ ! "$value" =~ ^[0-9]+$ ]]; then
            warn "OPNsense WAN baseline was invalid; remove $state_file to rebuild it"
            return
        fi
    done

    local reset=0
    if (( link_down < prev_link_down || local_faults < prev_local_faults ||
          remote_faults < prev_remote_faults || crc_errs < prev_crc_errs ||
          good_pkts_rcvd < prev_good_pkts_rcvd ||
          rx_missed_packets < prev_rx_missed_packets || xoff_txd < prev_xoff_txd ||
          link_irq < prev_link_irq )); then
        reset=1
    fi

    local link_down_delta=$((link_down - prev_link_down))
    local local_faults_delta=$((local_faults - prev_local_faults))
    local remote_faults_delta=$((remote_faults - prev_remote_faults))
    local crc_delta=$((crc_errs - prev_crc_errs))
    local good_delta=$((good_pkts_rcvd - prev_good_pkts_rcvd))
    local missed_delta=$((rx_missed_packets - prev_rx_missed_packets))
    local xoff_delta=$((xoff_txd - prev_xoff_txd))
    local link_irq_delta=$((link_irq - prev_link_irq))

    {
        printf 'link_down=%s\n' "$link_down"
        printf 'local_faults=%s\n' "$local_faults"
        printf 'remote_faults=%s\n' "$remote_faults"
        printf 'crc_errs=%s\n' "$crc_errs"
        printf 'good_pkts_rcvd=%s\n' "$good_pkts_rcvd"
        printf 'rx_missed_packets=%s\n' "$rx_missed_packets"
        printf 'xoff_txd=%s\n' "$xoff_txd"
        printf 'link_irq=%s\n' "$link_irq"
    } > "$state_file"

    if (( reset )); then
        warn "OPNsense WAN counters reset; baseline refreshed"
    elif (( link_down_delta > 0 || local_faults_delta > 0 ||
            remote_faults_delta > 0 || crc_delta > 0 || link_irq_delta > 0 )); then
        fail "OPNsense WAN physical counters increased: link-down +${link_down_delta}, local faults +${local_faults_delta}, remote faults +${remote_faults_delta}, CRC +${crc_delta}, link IRQ +${link_irq_delta}"
    elif (( missed_delta > 1000 && good_delta > 0 &&
            (missed_delta * 1000000 / good_delta) > 1000 )); then
        warn "OPNsense WAN RX-missed increased by ${missed_delta} packets relative to ${good_delta} received"
    else
        pass "OPNsense WAN active; physical counters unchanged (RX-missed +${missed_delta}, XOFF +${xoff_delta})"
    fi
}

check_arista() {
    local state_file="$STATE_ROOT/arista.state"
    local status_output
    local error_output
    local temperature_output
    local power_output
    local expected_ports=(
        "Et4:a-10G"
        "Et9:a-10G"
        "Et15:a-10G"
        "Et24:a-1G"
        "Et28:a-1G"
        "Et33:a-10G"
        "Et42:a-10G"
        "Et45:a-100M"
        "Et46:a-100M"
        "Et48:a-1G"
    )

    if ! status_output="$(ssh -o BatchMode=yes -o ConnectTimeout=5 arista 'show interfaces status')" ||
       ! error_output="$(ssh -o BatchMode=yes -o ConnectTimeout=5 arista 'show interfaces counters errors')" ||
       ! temperature_output="$(ssh -o BatchMode=yes -o ConnectTimeout=5 arista 'show environment temperature')" ||
       ! power_output="$(ssh -o BatchMode=yes -o ConnectTimeout=5 arista 'show environment power')"; then
        warn "Unable to collect Arista health data"
        return
    fi

    local spec
    local port
    local expected_speed
    local observed
    local port_status
    local port_speed
    local link_failures=()

    for spec in "${expected_ports[@]}"; do
        port="${spec%%:*}"
        expected_speed="${spec#*:}"
        observed="$(awk -v port="$port" '$1 == port {print $3 "|" $6; exit}' <<< "$status_output")"
        port_status="${observed%%|*}"
        port_speed="${observed#*|}"

        if [[ -z "$observed" || "$port_status" != "connected" ||
              "$port_speed" != "$expected_speed" ]]; then
            link_failures+=("$port=${port_status:-missing}/${port_speed:-unknown}")
        fi
    done

    local temperature_status
    temperature_status="$(awk -F': ' '/System temperature status is:/{print $2; exit}' <<< "$temperature_output")"

    local psu2_status
    psu2_status="$(awk '$1 == "2" && $2 ~ /^PWR-/ {print $7; exit}' <<< "$power_output")"

    if (( ${#link_failures[@]} > 0 )); then
        fail "Arista expected-link state changed: ${link_failures[*]}"
        return
    elif [[ "$temperature_status" != "Ok" ]]; then
        fail "Arista temperature status is ${temperature_status:-unknown}"
        return
    elif [[ "$psu2_status" != "Ok" ]]; then
        fail "Arista PSU2 status is ${psu2_status:-unknown}"
        return
    fi

    mkdir -p "$STATE_ROOT"

    local current_errors=()
    local error_total
    for spec in "${expected_ports[@]}"; do
        port="${spec%%:*}"
        error_total="$(awk -v port="$port" '
            $1 == port {
                total=0
                for (column=2; column<=8; column++) total += $column
                print total
                exit
            }
        ' <<< "$error_output")"

        if [[ ! "$error_total" =~ ^[0-9]+$ ]]; then
            warn "Arista error-counter output was incomplete for $port"
            return
        fi
        current_errors+=("$port=$error_total")
    done

    if [[ ! -f "$state_file" ]]; then
        printf '%s\n' "${current_errors[@]}" > "$state_file"
        pass "Arista links, temperature and PSU2 are healthy; error baseline recorded"
        return
    fi

    local reset=0
    local total_delta=0
    local error_deltas=()
    local previous
    local current
    local delta

    for observed in "${current_errors[@]}"; do
        port="${observed%%=*}"
        current="${observed#*=}"
        previous="$(awk -F'=' -v port="$port" '$1 == port {print $2; exit}' "$state_file")"

        if [[ ! "$previous" =~ ^[0-9]+$ ]]; then
            warn "Arista error baseline was invalid; remove $state_file to rebuild it"
            return
        fi

        delta=$((current - previous))
        if (( delta < 0 )); then
            reset=1
        elif (( delta > 0 )); then
            total_delta=$((total_delta + delta))
            error_deltas+=("$port +$delta")
        fi
    done

    printf '%s\n' "${current_errors[@]}" > "$state_file"

    if (( reset )); then
        warn "Arista interface counters reset; baseline refreshed"
    elif (( total_delta > 0 )); then
        fail "Arista interface errors increased: ${error_deltas[*]}"
    else
        pass "Arista expected links, temperature and PSU2 healthy; interface errors unchanged"
    fi
}

check_proxmox() {
    local node_json
    local guest_json
    local storage_output

    if ! node_json="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 proxmox \
            'pvesh get /nodes/$(hostname)/status --output-format json'
    )" ||
       ! guest_json="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 proxmox \
            'pvesh get /cluster/resources --type vm --output-format json'
    )" ||
       ! storage_output="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 proxmox 'pvesm status'
    )"; then
        warn "Unable to collect Proxmox health data"
        return
    fi

    local node_metrics
    if ! node_metrics="$(python3 -c '
import json, sys
data = json.load(sys.stdin)
memory = data["memory"]
swap = data["swap"]
root = data["rootfs"]
cores = int(data["cpuinfo"]["cpus"])
load1 = float(data["loadavg"][0])
print("memory_available_pct=%d" % (memory.get("available") * 100 // memory.get("total")))
print("swap_used_pct=%d" % (swap.get("used") * 100 // swap.get("total") if swap.get("total") else 0))
print("root_used_pct=%d" % (root.get("used") * 100 // root.get("total")))
print("load_per_core_pct=%d" % int(load1 * 100 / cores))
' <<< "$node_json")"; then
        warn "Unable to parse Proxmox node health data"
        return
    fi

    local memory_available_pct=""
    local swap_used_pct=""
    local root_used_pct=""
    local load_per_core_pct=""
    local key
    local value

    while IFS='=' read -r key value; do
        case "$key" in
            memory_available_pct) memory_available_pct="$value" ;;
            swap_used_pct) swap_used_pct="$value" ;;
            root_used_pct) root_used_pct="$value" ;;
            load_per_core_pct) load_per_core_pct="$value" ;;
        esac
    done <<< "$node_metrics"

    for value in "$memory_available_pct" "$swap_used_pct" "$root_used_pct" \
        "$load_per_core_pct"; do
        if [[ ! "$value" =~ ^[0-9]+$ ]]; then
            warn "Proxmox node health output was incomplete"
            return
        fi
    done

    local guest_status
    if ! guest_status="$(python3 -c '
import json, sys
for guest in json.load(sys.stdin):
    print("{}|{}|{}".format(guest.get("vmid"), guest.get("status"), guest.get("name", "unnamed")))
' <<< "$guest_json")"; then
        warn "Unable to parse Proxmox guest health data"
        return
    fi

    local failures=()
    local warnings=()
    local guest
    local guest_line
    local guest_state
    local guest_name

    for guest in 100 101 102 103 104; do
        guest_line="$(awk -F'|' -v guest="$guest" '$1 == guest {print; exit}' <<< "$guest_status")"
        guest_state="$(cut -d'|' -f2 <<< "$guest_line")"
        guest_name="$(cut -d'|' -f3 <<< "$guest_line")"

        if [[ -z "$guest_line" ]]; then
            failures+=("guest $guest missing")
        elif [[ "$guest_state" != "running" ]]; then
            failures+=("guest $guest ${guest_name:-unnamed}=$guest_state")
        fi
    done

    local storage
    local storage_line
    local storage_state
    local storage_used
    local highest_storage=0

    for storage in backups local local-lvm; do
        storage_line="$(awk -v storage="$storage" '$1 == storage {print; exit}' <<< "$storage_output")"
        storage_state="$(awk '{print $3}' <<< "$storage_line")"
        storage_used="$(awk '{gsub("%", "", $7); print int($7)}' <<< "$storage_line")"

        if [[ -z "$storage_line" ]]; then
            failures+=("storage $storage missing")
        elif [[ "$storage_state" != "active" ]]; then
            failures+=("storage $storage=$storage_state")
        elif [[ ! "$storage_used" =~ ^[0-9]+$ ]]; then
            warnings+=("storage $storage usage unknown")
        else
            (( storage_used > highest_storage )) && highest_storage="$storage_used"
            (( storage_used >= 90 )) && failures+=("storage $storage ${storage_used}% used")
            (( storage_used >= 80 && storage_used < 90 )) && warnings+=("storage $storage ${storage_used}% used")
        fi
    done

    (( memory_available_pct < 10 )) && failures+=("memory ${memory_available_pct}% available")
    (( memory_available_pct >= 10 && memory_available_pct < 20 )) && warnings+=("memory ${memory_available_pct}% available")
    (( swap_used_pct >= 90 )) && failures+=("swap ${swap_used_pct}% used")
    (( swap_used_pct >= 75 && swap_used_pct < 90 )) && warnings+=("swap ${swap_used_pct}% used")
    (( root_used_pct >= 90 )) && failures+=("root filesystem ${root_used_pct}% used")
    (( root_used_pct >= 80 && root_used_pct < 90 )) && warnings+=("root filesystem ${root_used_pct}% used")
    (( load_per_core_pct >= 400 )) && failures+=("one-minute load ${load_per_core_pct}% per core")
    (( load_per_core_pct >= 200 && load_per_core_pct < 400 )) && warnings+=("one-minute load ${load_per_core_pct}% per core")

    if (( ${#failures[@]} > 0 )); then
        fail "Proxmox health issue: ${failures[*]}"
    elif (( ${#warnings[@]} > 0 )); then
        warn "Proxmox resource warning: ${warnings[*]}"
    else
        pass "Proxmox guests and storage healthy; memory ${memory_available_pct}% available, swap ${swap_used_pct}% used, highest storage ${highest_storage}%"
    fi
}

check_nut() {
    local nut_output
    local server_state=""
    local monitor_state=""
    local ups_lines=""
    local expected_ups=(proxmox-ups nas-ups)

    if ! nut_output="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 nut /bin/bash -s <<'REMOTE'
printf 'server=%s\n' "$(systemctl is-active nut-server 2>/dev/null || true)"
printf 'monitor=%s\n' "$(systemctl is-active nut-monitor 2>/dev/null || true)"
for name in $(upsc -l 2>/dev/null); do
    status="$(upsc "$name@localhost" ups.status 2>/dev/null | tr ' ' '_')"
    charge="$(upsc "$name@localhost" battery.charge 2>/dev/null)"
    printf 'ups=%s|%s|%s\n' "$name" "${status:-unknown}" "${charge:-unknown}"
done
REMOTE
    )"; then
        warn "Unable to collect NUT health data"
        return
    fi

    while IFS='=' read -r key value; do
        case "$key" in
            server) server_state="$value" ;;
            monitor) monitor_state="$value" ;;
            ups) ups_lines+="$value"$'\n' ;;
        esac
    done <<< "$nut_output"

    local failures=()
    local warnings=()

    [[ "$server_state" != "active" ]] && failures+=("nut-server=${server_state:-unknown}")
    [[ "$monitor_state" != "active" ]] && failures+=("nut-monitor=${monitor_state:-unknown}")

    local name
    local status
    local charge
    local seen=()

    while IFS='|' read -r name status charge; do
        [[ -z "$name" ]] && continue
        seen+=("$name")
        if [[ "$status" != *OL* ]]; then
            failures+=("$name status=${status:-unknown}")
        fi
        if [[ "$charge" =~ ^[0-9]+$ ]] && (( charge < 50 )); then
            warnings+=("$name battery ${charge}%")
        fi
    done <<< "$ups_lines"

    local expected
    for expected in "${expected_ups[@]}"; do
        if ! printf '%s\n' "${seen[@]}" | grep -qx "$expected"; then
            failures+=("$expected not detected")
        fi
    done

    if (( ${#failures[@]} > 0 )); then
        fail "NUT health issue: ${failures[*]}"
    elif (( ${#warnings[@]} > 0 )); then
        warn "NUT degraded: ${warnings[*]}"
    else
        pass "NUT server, monitor and both UPS units healthy (${seen[*]})"
    fi
}

check_truenas() {
    local state_file="$STATE_ROOT/truenas-bond.state"
    local pool_json
    local bond_output
    local nfs_state
    local export_output

    if ! pool_json="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 truenas 'midclt call pool.query'
    )" ||
       ! bond_output="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 truenas 'cat /proc/net/bonding/bond0'
    )" ||
       ! nfs_state="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 truenas 'systemctl is-active nfs-server'
    )" ||
       ! export_output="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 truenas 'exportfs -v'
    )"; then
        warn "Unable to collect TrueNAS health data"
        return
    fi

    local pool_status
    if ! pool_status="$(python3 -c '
import json, sys
for pool in json.load(sys.stdin):
    size = int(pool.get("size") or 0)
    allocated = int(pool.get("allocated") or 0)
    used = allocated * 100 // size if size else 0
    print("{}|{}|{}|{}".format(
        pool.get("name", "unnamed"),
        pool.get("status", "unknown"),
        str(bool(pool.get("healthy"))).lower(),
        used,
    ))
' <<< "$pool_json")"; then
        warn "Unable to parse TrueNAS pool health data"
        return
    fi

    local failures=()
    local warnings=()
    local pool_name
    local pool_state
    local pool_healthy
    local pool_used
    local highest_pool=0

    while IFS='|' read -r pool_name pool_state pool_healthy pool_used; do
        [[ -z "$pool_name" ]] && continue
        if [[ "$pool_state" != "ONLINE" || "$pool_healthy" != "true" ]]; then
            failures+=("pool $pool_name=$pool_state/healthy:$pool_healthy")
        elif [[ ! "$pool_used" =~ ^[0-9]+$ ]]; then
            warnings+=("pool $pool_name usage unknown")
        else
            (( pool_used > highest_pool )) && highest_pool="$pool_used"
            (( pool_used >= 90 )) && failures+=("pool $pool_name ${pool_used}% used")
            (( pool_used >= 80 && pool_used < 90 )) && warnings+=("pool $pool_name ${pool_used}% used")
        fi
    done <<< "$pool_status"

    if [[ -z "$pool_status" ]]; then
        failures+=("no pools reported")
    fi

    local bond_state
    local active_slave
    bond_state="$(awk -F': ' '/^MII Status:/{print $2; exit}' <<< "$bond_output")"
    active_slave="$(awk -F': ' '/^Currently Active Slave:/{print $2; exit}' <<< "$bond_output")"

    if [[ "$bond_state" != "up" ]]; then
        failures+=("bond0=$bond_state")
    elif [[ "$active_slave" != "enp5s0f0" ]]; then
        warnings+=("bond0 active slave=${active_slave:-unknown}")
    fi

    local slave_status
    slave_status="$(awk -F': ' '
        /^Slave Interface:/ {slave=$2}
        /^MII Status:/ && slave != "" {print slave "=" $2; slave=""}
    ' <<< "$bond_output")"

    local slave
    local observed_state
    for slave in enp5s0f0 enp5s0f1; do
        observed_state="$(awk -F'=' -v slave="$slave" '$1 == slave {print $2; exit}' <<< "$slave_status")"
        [[ "$observed_state" != "up" ]] && warnings+=("$slave=${observed_state:-missing}")
    done

    if [[ "$nfs_state" != "active" ]]; then
        failures+=("NFS service=$nfs_state")
    fi
    if ! grep -Fq '/mnt/Media/Surveillance/Frigate' <<< "$export_output"; then
        failures+=("Frigate NFS export missing")
    fi

    mkdir -p "$STATE_ROOT"

    local failure_counts
    failure_counts="$(awk -F': ' '
        /^Slave Interface:/ {slave=$2}
        /^Link Failure Count:/ && slave != "" {print slave "=" $2; slave=""}
    ' <<< "$bond_output")"

    local current_primary
    local current_secondary
    current_primary="$(awk -F'=' '$1 == "enp5s0f0" {print $2; exit}' <<< "$failure_counts")"
    current_secondary="$(awk -F'=' '$1 == "enp5s0f1" {print $2; exit}' <<< "$failure_counts")"

    if [[ ! "$current_primary" =~ ^[0-9]+$ || ! "$current_secondary" =~ ^[0-9]+$ ]]; then
        warnings+=("bond failure counters unavailable")
    elif [[ ! -f "$state_file" ]]; then
        printf 'enp5s0f0=%s\nenp5s0f1=%s\n' "$current_primary" "$current_secondary" > "$state_file"
    else
        local previous_primary
        local previous_secondary
        previous_primary="$(awk -F'=' '$1 == "enp5s0f0" {print $2; exit}' "$state_file")"
        previous_secondary="$(awk -F'=' '$1 == "enp5s0f1" {print $2; exit}' "$state_file")"

        if [[ ! "$previous_primary" =~ ^[0-9]+$ || ! "$previous_secondary" =~ ^[0-9]+$ ]]; then
            warnings+=("bond baseline invalid")
        elif (( current_primary < previous_primary || current_secondary < previous_secondary )); then
            warnings+=("bond counters reset")
        elif (( current_primary > previous_primary || current_secondary > previous_secondary )); then
            warnings+=("bond link failures increased: primary +$((current_primary - previous_primary)), secondary +$((current_secondary - previous_secondary))")
        fi

        printf 'enp5s0f0=%s\nenp5s0f1=%s\n' "$current_primary" "$current_secondary" > "$state_file"
    fi

    if (( ${#failures[@]} > 0 )); then
        fail "TrueNAS health issue: ${failures[*]}"
    elif (( ${#warnings[@]} > 0 )); then
        warn "TrueNAS degraded: ${warnings[*]}"
    elif [[ -f "$state_file" ]]; then
        pass "TrueNAS pools, NFS and bond healthy; ${highest_pool}% highest pool use, primary link active"
    fi
}

check_frigate() {
    local frigate_output
    local service_state=""
    local mount_source=""
    local mount_type=""
    local newest_recording=""

    if ! frigate_output="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 frigate /bin/bash -s <<'REMOTE'
printf 'service=%s\n' "$(systemctl is-active frigate-compose.service 2>/dev/null || true)"
findmnt -rn -T /opt/frigate/storage -o SOURCE,FSTYPE 2>/dev/null |
    awk '$2 == "nfs4" {print "mount_source=" $1; print "mount_type=" $2; exit}'
printf 'newest_recording=%s\n' "$(
    find /opt/frigate/storage/recordings -type f -name '*.mp4' -printf '%T@\n' 2>/dev/null |
        sort -n |
        tail -1
)"
REMOTE
    )"; then
        warn "Unable to collect Frigate health data"
        return
    fi

    while IFS='=' read -r key value; do
        case "$key" in
            service) service_state="$value" ;;
            mount_source) mount_source="$value" ;;
            mount_type) mount_type="$value" ;;
            newest_recording) newest_recording="$value" ;;
        esac
    done <<< "$frigate_output"

    if [[ "$service_state" != "active" ]]; then
        fail "Frigate compose service is ${service_state:-unknown}"
        return
    fi

    if [[ "$mount_type" != "nfs4" || "$mount_source" != "192.168.20.40:/mnt/Media/Surveillance/Frigate" ]]; then
        fail "Frigate recording storage is not mounted from the expected TrueNAS NFS export"
        return
    fi

    if [[ ! "$newest_recording" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
        fail "Frigate has no readable MP4 recordings"
        return
    fi

    local now_epoch
    local recording_epoch
    local recording_age
    now_epoch="$(date +%s)"
    recording_epoch="${newest_recording%%.*}"
    recording_age=$((now_epoch - recording_epoch))

    if (( recording_age < 0 )); then
        warn "Frigate recording timestamp is ahead of the Mac clock"
    elif (( recording_age > 900 )); then
        fail "Frigate newest recording is $((recording_age / 60)) minute(s) old"
    elif (( recording_age > 300 )); then
        warn "Frigate newest recording is $((recording_age / 60)) minute(s) old"
    else
        pass "Frigate service, NFS storage and recording flow healthy; newest recording is $((recording_age / 60)) minute(s) old"
    fi
}

header "HomeLab Doctor"

info "Checking internet connectivity..."

if nc -z -G 5 1.1.1.1 443 >/dev/null 2>&1; then
    pass "Internet connectivity"
else
    fail "Internet connectivity"
fi

check_opnsense_wan
check_arista
check_proxmox
check_hermes
check_nut
check_truenas
check_frigate

divider

info "Checking DNS resolution..."

if dscacheutil -q host -a name github.com 2>/dev/null | grep -q 'ip_address'; then
    pass "DNS resolution"
else
    fail "DNS resolution"
fi

check_pihole_dns "Pi-hole Primary" "192.168.20.20"
check_pihole_dns "Pi-hole Secondary" "192.168.20.40"

divider

info "Checking configured services..."

if [[ -f "$SERVICES_CONFIG" ]]; then
    while IFS='|' read -r name display ip port; do
        [[ -z "$name" || "$name" == \#* ]] && continue
        check_tcp "$display" "$ip" "$port"
    done < "$SERVICES_CONFIG"
else
    warn "Service configuration not found"
fi

divider

info "Checking configuration backups..."

check_backup_age "OPNsense" "$BACKUP_ROOT/opnsense" 48
check_backup_age "Arista" "$BACKUP_ROOT/arista" 48
check_backup_age "Proxmox" "$BACKUP_ROOT/proxmox" 48
check_backup_age "NUT" "$BACKUP_ROOT/nut" 48
check_proxmox_guest_backup_age "Home Assistant VM 103" 103 30
check_proxmox_guest_backup_age "Hermes LXC 104" 104 30 lxc
check_proxmox_guest_backup_age "Ollama VM 105" 105 30
check_reported_backup "Configuration pull to Backup Synology" "synology-pull" 30
check_reported_backup "Proxmox guest pull to Backup Synology" "proxmox-pull" 30

divider

info "Checking Mac disk usage..."

DISK_PERCENT="$(
    df -Pk "$HOME" |
    awk 'NR == 2 {gsub("%", "", $5); print $5}'
)"

if [[ -z "$DISK_PERCENT" ]]; then
    warn "Unable to determine disk usage"
elif (( DISK_PERCENT < 80 )); then
    pass "Mac disk usage is ${DISK_PERCENT}%"
elif (( DISK_PERCENT < 90 )); then
    warn "Mac disk usage is ${DISK_PERCENT}%"
else
    fail "Mac disk usage is ${DISK_PERCENT}%"
fi

divider

info "Checking Git repository..."

if [[ ! -d "$REPO/.git" ]]; then
    fail "HomeLab Git repository not found"
else
    GIT_STATUS="$(git -C "$REPO" status --porcelain 2>/dev/null)"

    if [[ -z "$GIT_STATUS" ]]; then
        pass "Git working tree is clean"
    else
        warn "Git repository contains uncommitted changes"
    fi

    if git -C "$REPO" remote get-url origin >/dev/null 2>&1; then
        pass "Git remote is configured"
    else
        warn "Git remote is not configured"
    fi
fi

divider

echo "Summary"
echo
echo "🟢 Passed:   $PASS_COUNT"
echo "🟡 Warnings: $WARN_COUNT"
echo "🔴 Failed:   $FAIL_COUNT"
echo

if (( FAIL_COUNT > 0 )); then
    error "HomeLab doctor found one or more failures"
    exit 1
elif (( WARN_COUNT > 0 )); then
    warning "HomeLab is operational with warnings"
    exit 0
else
    success "HomeLab is healthy"
    exit 0
fi
