#!/usr/bin/env python3
"""Run the fixed one-frame MuseTalk/MLX probe behind hard memory gates."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "musetalk_probe_manifest.json"
LIGHTROOM_PROCESS = (
    "/Applications/Adobe Lightroom Classic/Adobe Lightroom Classic.app/Contents/"
    "MacOS/Adobe Lightroom Classic"
)
BROWSER_PROCESSES = (
    "/Applications/Safari.app/Contents/MacOS/Safari",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Firefox.app/Contents/MacOS/firefox",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)
LOCAL_AI_ROOT = Path.home() / "Library/Application Support/Aster Local AI"
WHOLE_HOST_LEASE_LOCK = LOCAL_AI_ROOT / "whole-host.lease.lock"
SHARED_OPERATION_LOCK = LOCAL_AI_ROOT / "shared-operation.lock"


class ProbeError(RuntimeError):
    pass


def acquire_exclusion_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        if info.st_uid != os.getuid() or info.st_nlink != 1 or info.st_mode & 0o077:
            raise ProbeError(f"unsafe local AI lock custody: {path.name}")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        os.close(descriptor)
        raise ProbeError(f"local AI exclusion is already held: {path.name}") from error
    except BaseException:
        os.close(descriptor)
        raise
    return os.fdopen(descriptor, "r+")


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "aster.news-video-musetalk-probe.v1":
        raise ProbeError("unsupported probe manifest")
    if manifest.get("status") != "staged-attended-probe":
        raise ProbeError("this MuseTalk probe is rejected on the 16 GiB M4 host")
    probe = manifest["probe"]
    safety = manifest["safety"]
    admission = manifest["admission"]
    if probe.get("frames") != 1 or probe.get("batch_size") != 1:
        raise ProbeError("the first resource-ladder probe must remain one frame at batch one")
    if manifest.get("production_enabled") is not False:
        raise ProbeError("the probe may not be production enabled")
    if admission != {
        "execution_host": "mac-mlx",
        "b60_lab_hours_required": False,
        "attended_probe_only": True,
    }:
        raise ProbeError("Mac-only attended admission contract drifted")
    if safety.get("minimum_free_percent_at_start", 0) < 40:
        raise ProbeError("start-memory floor may not be below 40 percent")
    if safety.get("minimum_free_percent_while_running", 0) < 20:
        raise ProbeError("runtime-memory floor may not be below 20 percent")
    if safety.get("maximum_process_tree_rss_bytes", 0) > 6 * 1024**3:
        raise ProbeError("process-tree RSS ceiling may not exceed 6 GiB")
    if safety.get("maximum_swap_used_mb_at_start", 0) > 768:
        raise ProbeError("starting swap ceiling may not exceed 768 MiB")
    if safety.get("maximum_swap_growth_mb") != 0:
        raise ProbeError("the probe may not permit new swap growth")
    return manifest


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_input(manifest_path: Path, record: dict[str, str]) -> Path:
    path = (manifest_path.parent / record["path"]).resolve()
    if not path.is_file() or sha256(path) != record["sha256"]:
        raise ProbeError(f"input missing or hash mismatch: {path}")
    return path


def verify_model(manifest: dict[str, Any], model_root: Path) -> None:
    expected = manifest["model"]["files"]
    actual = {item.name for item in model_root.iterdir() if item.is_file()}
    if actual != set(expected):
        raise ProbeError("model file set does not match the pinned snapshot")
    for name, expected_hash in expected.items():
        path = model_root / name
        if path.is_symlink() or sha256(path) != expected_hash:
            raise ProbeError(f"model hash mismatch: {name}")


def verify_source(manifest: dict[str, Any], source_root: Path) -> None:
    source = manifest["source"]
    if not source_root.is_dir() or source_root.is_symlink():
        raise ProbeError("pinned MuseTalk source root is unavailable")
    head = subprocess.run(
        ["/usr/bin/git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    listing = subprocess.run(
        ["/usr/bin/git", "-C", str(source_root), "ls-tree", "-r", "HEAD"],
        check=True,
        capture_output=True,
    ).stdout
    dirty = subprocess.run(
        ["/usr/bin/git", "-C", str(source_root), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    tree_hash = hashlib.sha256(listing).hexdigest()
    if head != source["revision"] or tree_hash != source["tree_sha256"] or dirty:
        raise ProbeError("MuseTalk source revision, tree hash, or cleanliness drifted")


def memory_free_percent() -> int:
    output = subprocess.run(
        ["/usr/bin/memory_pressure", "-Q"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    match = re.search(r"System-wide memory free percentage:\s*(\d+)%", output)
    if not match:
        raise ProbeError("could not read system memory pressure")
    return int(match.group(1))


def swap_used_mb() -> float:
    output = subprocess.run(
        ["/usr/sbin/sysctl", "vm.swapusage"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    match = re.search(r"used\s*=\s*([0-9.]+)M", output)
    if not match:
        raise ProbeError("could not read swap use")
    return float(match.group(1))


def process_rows() -> list[tuple[int, int, int, str]]:
    output = subprocess.run(
        ["/bin/ps", "-axo", "pid=,ppid=,rss=,command="],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    rows = []
    for line in output.splitlines():
        parts = line.strip().split(maxsplit=3)
        if len(parts) == 4:
            rows.append((int(parts[0]), int(parts[1]), int(parts[2]), parts[3]))
    return rows


def forbidden_processes(rows: list[tuple[int, int, int, str]]) -> list[str]:
    matches = []
    for _pid, _ppid, _rss, command in rows:
        paths = (LIGHTROOM_PROCESS, *BROWSER_PROCESSES)
        if any(command == path or command.startswith(path + " ") for path in paths):
            matches.append(command)
    return matches


def process_tree_rss_bytes(root_pid: int, rows: list[tuple[int, int, int, str]]) -> int:
    children: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    for pid, ppid, rss_kb, _command in rows:
        children.setdefault(ppid, []).append(pid)
        rss[pid] = rss_kb
    pending = [root_pid]
    selected = set()
    while pending:
        pid = pending.pop()
        if pid in selected:
            continue
        selected.add(pid)
        pending.extend(children.get(pid, []))
    return sum(rss.get(pid, 0) for pid in selected) * 1024


def preflight(manifest: dict[str, Any]) -> dict[str, float | int]:
    safety = manifest["safety"]
    rows = process_rows()
    forbidden = forbidden_processes(rows)
    if forbidden:
        raise ProbeError("Lightroom or a browser is open")
    free = memory_free_percent()
    swap = swap_used_mb()
    if free < safety["minimum_free_percent_at_start"]:
        raise ProbeError(f"only {free}% memory free; refusing model load")
    if swap > safety["maximum_swap_used_mb_at_start"]:
        raise ProbeError(f"starting swap exceeds the bounded baseline: {swap} MB")
    return {"free_percent": free, "swap_used_mb": swap}


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def worker(manifest_path: Path, source_root: Path, model_root: Path, output_dir: Path) -> int:
    sys.path.insert(0, str(source_root))
    import cv2
    import mlx.core as mx
    import mlx.nn as nn

    from musetalk_mlx.pipeline_mlx import MuseTalkPipeline
    from musetalk_mlx.models.unet import UNet2DConditionModel
    from musetalk_mlx.models.vae import AutoencoderKL
    from musetalk_mlx.utils.weights import load_native
    from musetalk_mlx.whisper.whisper_encoder import WhisperEncoder

    manifest = load_manifest(manifest_path)
    verify_model(manifest, model_root)
    image_path = resolve_input(manifest_path, manifest["inputs"]["studio_image"])
    audio_path = resolve_input(manifest_path, manifest["inputs"]["audio"])
    output_dir.mkdir(parents=True, exist_ok=False)

    frame = cv2.imread(str(image_path))
    if frame is None:
        raise ProbeError("could not decode studio image")
    x1, y1, x2, y2 = manifest["inputs"]["face_crop_xyxy"]
    if not (0 <= x1 < x2 <= frame.shape[1] and 0 <= y1 < y2 <= frame.shape[0]):
        raise ProbeError("face crop is outside the studio image")
    crop = cv2.resize(frame[y1:y2, x1:x2], (256, 256), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(output_dir / "input-face.png"), crop)

    mx.set_default_device(mx.gpu)
    meta = json.loads((model_root / "config.json").read_text(encoding="utf-8"))
    started = time.monotonic()

    # Load and materialize the three networks in dependency order. The original
    # helper materializes Whisper, VAE and UNet together, creating an avoidable
    # Metal-memory peak on a 16 GiB Mac.
    whisper = WhisperEncoder()
    load_native(whisper, model_root / "whisper_encoder.safetensors")
    whisper.eval()
    mx.eval(whisper.parameters())
    audio_pipe = MuseTalkPipeline(
        vae=None, unet=None, whisper_encoder=whisper,
        scaling_factor=meta.get("scaling_factor"),
    )
    chunks = audio_pipe.encode_audio_from_wav(audio_path, fps=manifest["probe"]["fps"])[0:1]
    mx.eval(chunks)
    audio_ready = time.monotonic()
    del audio_pipe, whisper
    mx.clear_cache()

    vae = AutoencoderKL()
    load_native(vae, model_root / "vae.safetensors")
    vae.eval()
    mx.eval(vae.parameters())
    pipe = MuseTalkPipeline(
        vae=vae, unet=None, whisper_encoder=None,
        scaling_factor=meta.get("scaling_factor"),
    )
    pipe._dtype = mx.float16 if meta.get("dtype") == "float16" else mx.bfloat16
    latent = pipe.get_latents_for_unet(crop)
    mx.eval(latent)
    latent_ready = time.monotonic()

    unet = UNet2DConditionModel()
    quantization = meta.get("quantization")
    if quantization:
        nn.quantize(unet, group_size=quantization["group_size"], bits=quantization["bits"])
    load_native(unet, model_root / "unet.safetensors")
    unet.eval()
    mx.eval(unet.parameters())
    pipe.unet = unet
    loaded = time.monotonic()
    prepared = time.monotonic()
    result = pipe.run_batched(latent, chunks[:1], batch_size=1)
    mx.synchronize()
    finished = time.monotonic()
    cv2.imwrite(str(output_dir / "generated-face.png"), result[0])

    report = {
        "schema": "aster.news-video-musetalk-probe-result.v1",
        "status": "candidate",
        "frames": 1,
        "batch_size": 1,
        "timing_seconds": {
            "audio_encode": round(audio_ready - started, 4),
            "vae_and_latent": round(latent_ready - audio_ready, 4),
            "unet_load": round(loaded - latent_ready, 4),
            "input_preparation": round(prepared - loaded, 4),
            "generation": round(finished - prepared, 4),
            "total": round(finished - started, 4),
        },
        "mlx_peak_memory_bytes": mx.get_peak_memory(),
        "input_face_sha256": sha256(output_dir / "input-face.png"),
        "generated_face_sha256": sha256(output_dir / "generated-face.png"),
    }
    atomic_json(output_dir / "worker-result.json", report)
    return 0


def supervise(manifest_path: Path, source_root: Path, model_root: Path) -> int:
    with ExitStack() as locks:
        locks.enter_context(acquire_exclusion_lock(WHOLE_HOST_LEASE_LOCK))
        locks.enter_context(acquire_exclusion_lock(SHARED_OPERATION_LOCK))
        return supervise_locked(manifest_path, source_root, model_root)


def supervise_locked(manifest_path: Path, source_root: Path, model_root: Path) -> int:
    manifest = load_manifest(manifest_path)
    verify_source(manifest, source_root)
    verify_model(manifest, model_root)
    initial = preflight(manifest)
    probe = manifest["probe"]
    safety = manifest["safety"]
    output_root = Path(probe["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    output_dir = output_root / time.strftime("%Y%m%dT%H%M%S")
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--manifest",
        str(manifest_path),
        "--source-root",
        str(source_root),
        "--model-root",
        str(model_root),
        "--output-dir",
        str(output_dir),
    ]
    child = subprocess.Popen(command, start_new_session=True)
    samples = []
    reason = None
    deadline = time.monotonic() + probe["timeout_seconds"]
    while child.poll() is None:
        rows = process_rows()
        sample = {
            "elapsed_seconds": round(probe["timeout_seconds"] - max(deadline - time.monotonic(), 0), 2),
            "free_percent": memory_free_percent(),
            "swap_used_mb": swap_used_mb(),
            "process_tree_rss_bytes": process_tree_rss_bytes(child.pid, rows),
        }
        samples.append(sample)
        if forbidden_processes(rows):
            reason = "Lightroom or a browser opened during the probe"
        elif sample["free_percent"] < safety["minimum_free_percent_while_running"]:
            reason = "system free-memory floor crossed"
        elif sample["swap_used_mb"] > initial["swap_used_mb"] + safety["maximum_swap_growth_mb"]:
            reason = "swap grew beyond the starting baseline"
        elif sample["process_tree_rss_bytes"] > safety["maximum_process_tree_rss_bytes"]:
            reason = "process-tree RSS ceiling crossed"
        elif time.monotonic() >= deadline:
            reason = "probe timeout"
        if reason:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            break
        time.sleep(0.5)

    supervisor = {
        "schema": "aster.news-video-musetalk-supervisor.v1",
        "status": "aborted" if reason else ("complete" if child.returncode == 0 else "failed"),
        "reason": reason,
        "initial": initial,
        "returncode": child.returncode,
        "samples": samples,
    }
    if output_dir.exists():
        atomic_json(output_dir / "supervisor-result.json", supervisor)
    if reason:
        raise ProbeError(reason)
    if child.returncode != 0 or not (output_dir / "worker-result.json").is_file():
        raise ProbeError("worker failed without a complete result")
    print(json.dumps({"output_dir": str(output_dir), **supervisor}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--model-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--output-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)
    source_root = Path(manifest["source"]["path"]).resolve()
    model_root = Path(manifest["model"]["path"]).resolve()
    if args.source_root is not None and args.source_root.resolve() != source_root:
        raise ProbeError("worker source root differs from the fixed manifest")
    if args.model_root is not None and args.model_root.resolve() != model_root:
        raise ProbeError("worker model root differs from the fixed manifest")
    verify_source(manifest, source_root)
    verify_model(manifest, model_root)
    if args.preflight_only:
        print(json.dumps(preflight(manifest), sort_keys=True))
        return 0
    if args.worker:
        if args.output_dir is None:
            raise ProbeError("worker output directory is required")
        return worker(manifest_path, source_root, model_root, args.output_dir.resolve())
    return supervise(manifest_path, source_root, model_root)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ProbeError as error:
        print(f"probe refused: {error}", file=sys.stderr)
        raise SystemExit(2)
