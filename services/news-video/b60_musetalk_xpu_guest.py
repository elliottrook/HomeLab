#!/opt/aster-news-video-xpu/venv/bin/python
"""Run the fixed 1.68-second Aster MuseTalk XPU compatibility render."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import cv2
import imageio_ffmpeg
import numpy as np
import torch
from transformers import WhisperModel


ROOT = Path("/opt/aster-news-video-xpu")
SOURCE = ROOT / "source/MuseTalk"
MODELS = ROOT / "models"
INPUT_IMAGE = ROOT / "inputs/studio.png"
INPUT_AUDIO = ROOT / "inputs/audio.wav"
OUTPUTS = ROOT / "outputs"
WORKLOAD_ID = "aster-news-video-musetalk-xpu-smoke-v1"
SOURCE_COMMIT = "3bd654938926af520ee30dfe945e4845ef476d94"
SOURCE_TREE = "0d61fc23223f0c54348c04dddbcb05a67f63c565"
FPS = 25
BATCH_SIZE = 4
CROP = (360, 20, 720, 380)
SHA = re.compile(r"[0-9a-f]{64}")
PINS = {
    INPUT_IMAGE: "fe85bb5cb3966661cc87827f42fb0a5672364873a6a818ece3a01da159a3bf64",
    INPUT_AUDIO: "f35338879433e2982fcffea358b2219a456cfa79cf607f1607989bd6bbf0934f",
    MODELS / "musetalkV15/musetalk.json": "5b6923aee04d71692e0e9846c471e0a4ea07a4f686d39545e472bd4ba17e1b47",
    MODELS / "musetalkV15/unet.pth": "7ebf6c98c181e20838e4c0054e96e944ac60d5d692cc01db42839fe11b787007",
    MODELS / "sd-vae/config.json": "92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e",
    MODELS / "sd-vae/diffusion_pytorch_model.bin": "1b4889b6b1d4ce7ae320a02dedaeff1780ad77d415ea0d744b476155c6377ddc",
    MODELS / "whisper/config.json": "ffdccec4f3211f4c63310f2b7098f309fe70f3952cedc5e4d11e43f5b2379b98",
    MODELS / "whisper/preprocessor_config.json": "9b5cd03a36fbb8a627c64d98a5b5b126ead95a77720723944487311f0110b666",
    MODELS / "whisper/pytorch_model.bin": "9607f98a2b22d9e229ae43c52ecea79dcede9e0c5cfae67e8da6eda86d8aac1d",
}


class RenderError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify() -> None:
    for path, expected in PINS.items():
        if not path.is_file() or path.is_symlink() or sha256(path) != expected:
            raise RenderError(f"PIN_DRIFT:{path.name}")
    head = subprocess.run(
        ("git", "-C", str(SOURCE), "rev-parse", "HEAD"),
        capture_output=True, text=True, timeout=10, check=False,
    )
    tree = subprocess.run(
        ("git", "-C", str(SOURCE), "rev-parse", "HEAD^{tree}"),
        capture_output=True, text=True, timeout=10, check=False,
    )
    if head.returncode or head.stdout.strip() != SOURCE_COMMIT:
        raise RenderError("SOURCE_COMMIT_DRIFT")
    if tree.returncode or tree.stdout.strip() != SOURCE_TREE:
        raise RenderError("SOURCE_TREE_DRIFT")


def blend_lower_face(frame: np.ndarray, generated: np.ndarray) -> np.ndarray:
    x1, y1, x2, y2 = CROP
    face = cv2.resize(generated, (x2 - x1, y2 - y1), interpolation=cv2.INTER_LANCZOS4)
    height, width = face.shape[:2]
    mask = np.zeros((height, width), dtype=np.float32)
    top = int(height * 0.40)
    mask[top:, :] = 1.0
    edge = max(17, int(width * 0.06))
    mask = cv2.GaussianBlur(mask, (edge | 1, edge | 1), 0)
    horizontal = np.ones((height, width), dtype=np.float32)
    horizontal[:, :edge] = np.linspace(0, 1, edge, dtype=np.float32)
    horizontal[:, -edge:] = np.linspace(1, 0, edge, dtype=np.float32)
    alpha = np.clip(mask * horizontal, 0, 1)[..., None]
    result = frame.copy()
    base = result[y1:y2, x1:x2].astype(np.float32)
    result[y1:y2, x1:x2] = np.clip(face.astype(np.float32) * alpha + base * (1 - alpha), 0, 255).astype(np.uint8)
    return result


def render(lease_id: str, generation: int) -> dict[str, object]:
    verify()
    if os.environ.get("MUSETALK_DEVICE") != "xpu:0":
        raise RenderError("DEVICE_NOT_FORCED")
    if not hasattr(torch, "xpu") or not torch.xpu.is_available():
        raise RenderError("XPU_UNAVAILABLE")
    device = torch.device("xpu:0")
    device_name = torch.xpu.get_device_name(0)
    if "Intel" not in device_name and "BMG" not in device_name:
        raise RenderError("XPU_IDENTITY")

    sys.path.insert(0, str(SOURCE))
    from musetalk.utils.audio_processor import AudioProcessor
    from musetalk.utils.utils import datagen, load_all_model

    image = cv2.imread(str(INPUT_IMAGE), cv2.IMREAD_COLOR)
    if image is None:
        raise RenderError("INPUT_DECODE")
    x1, y1, x2, y2 = CROP
    if image.shape[1] < x2 or image.shape[0] < y2:
        raise RenderError("CROP_OUTSIDE_INPUT")
    crop = cv2.resize(image[y1:y2, x1:x2], (256, 256), interpolation=cv2.INTER_LANCZOS4)

    started = time.monotonic()
    with contextlib.redirect_stdout(sys.stderr):
        vae, unet, pe = load_all_model(
            unet_model_path=str(MODELS / "musetalkV15/unet.pth"),
            vae_type=str(MODELS / "sd-vae"),
            unet_config=str(MODELS / "musetalkV15/musetalk.json"),
            device=device,
        )
        pe = pe.half().to(device)
        vae.vae = vae.vae.half().to(device)
        unet.model = unet.model.half().to(device).eval()
        audio = AudioProcessor(feature_extractor_path=str(MODELS / "whisper"))
        whisper = WhisperModel.from_pretrained(str(MODELS / "whisper"))
        whisper = whisper.to(device=device, dtype=torch.float16).eval()
        whisper.requires_grad_(False)
        features, sample_count = audio.get_audio_feature(str(INPUT_AUDIO))
        chunks = audio.get_whisper_chunk(
            features, device, torch.float16, whisper, sample_count, fps=FPS,
            audio_padding_length_left=2, audio_padding_length_right=2,
        )
        latent = vae.get_latents_for_unet(crop)
        generator = datagen(chunks, [latent], batch_size=BATCH_SIZE, device=device)
        timesteps = torch.tensor([0], device=device)
        generated_frames: list[np.ndarray] = []
        with torch.inference_mode():
            for whisper_batch, latent_batch in generator:
                encoded = pe(whisper_batch)
                predicted = unet.model(
                    latent_batch.to(dtype=torch.float16), timesteps,
                    encoder_hidden_states=encoded,
                ).sample
                generated_frames.extend(vae.decode_latents(predicted))
        torch.xpu.synchronize()

    safe_lease = re.sub(r"[^A-Za-z0-9_.-]", "-", lease_id)
    frame_dir = OUTPUTS / f"frames-{safe_lease}-{generation}"
    frame_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    for index, generated in enumerate(generated_frames):
        output = blend_lower_face(image, generated)
        if not cv2.imwrite(str(frame_dir / f"{index:08d}.png"), output):
            raise RenderError("FRAME_WRITE")

    video_only = OUTPUTS / f"video-{safe_lease}-{generation}.mp4"
    final = OUTPUTS / f"aster-musetalk-xpu-{safe_lease}-{generation}.mp4"
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    encode = subprocess.run(
        (ffmpeg, "-y", "-v", "error", "-framerate", str(FPS), "-i",
         str(frame_dir / "%08d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "18", str(video_only)), timeout=300, check=False,
    )
    if encode.returncode:
        raise RenderError("VIDEO_ENCODE")
    mux = subprocess.run(
        (ffmpeg, "-y", "-v", "error", "-i", str(video_only), "-i", str(INPUT_AUDIO),
         "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)), timeout=120, check=False,
    )
    if mux.returncode or not final.is_file():
        raise RenderError("AUDIO_MUX")
    elapsed = time.monotonic() - started
    return {
        "schema": "aster-news-video-musetalk-xpu-result.v1",
        "workload_id": WORKLOAD_ID,
        "lease_id": lease_id,
        "generation": generation,
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "torch_version": torch.__version__,
        "device": "xpu:0",
        "device_name": device_name,
        "fps": FPS,
        "batch_size": BATCH_SIZE,
        "frame_count": len(generated_frames),
        "render_seconds": round(elapsed, 4),
        "xpu_max_memory_allocated": int(torch.xpu.max_memory_allocated(0)),
        "output_path": str(final),
        "output_bytes": final.stat().st_size,
        "output_sha256": sha256(final),
        "network_used_during_render": False,
        "production_route_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workload-id", required=True)
    parser.add_argument("--lease-id", required=True)
    parser.add_argument("--generation", required=True, type=int)
    args = parser.parse_args()
    try:
        if args.workload_id != WORKLOAD_ID or args.generation < 1:
            raise RenderError("WORKLOAD_IDENTITY")
        result = render(args.lease_id, args.generation)
        print(json.dumps(result, sort_keys=True), flush=True)
        return 0
    except BaseException as exc:
        code = str(exc) if isinstance(exc, RenderError) else type(exc).__name__
        print(json.dumps({"code": re.sub(r"[^A-Za-z0-9_:-]", "_", code)[:120]}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
