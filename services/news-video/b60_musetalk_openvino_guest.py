#!/opt/aster-news-video-xpu/ov-venv/bin/python
"""Run the fixed Aster MuseTalk smoke render with OpenVINO on B60."""

from __future__ import annotations

import contextlib
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
import openvino as ov
import torch
from transformers import WhisperModel

import b60_musetalk_xpu_guest as common


WORKLOAD_ID = "aster-news-video-musetalk-openvino-smoke-v1"
IR_XML = common.MODELS / "openvino/musetalk-v15-unet-pe-b4.xml"
IR_BIN = IR_XML.with_suffix(".bin")
IR_XML_SHA256 = "40f7a284f0336457fd6fcc20f4e49ee77b435ca0c33a956a4a73146d8eda9f72"
IR_BIN_SHA256 = "7b5bab7795cd28b54a4dcf1ad62dd811dc787226f89e69ce11612335b94209fe"
OPENVINO_VERSION = "2026.4.1-22982-e213a147257-releases/2026/4"
OPENVINO_PYTHON = Path("/opt/aster-news-video-xpu/ov-venv/lib/python3.12/site-packages/openvino/_pyopenvino.cpython-312-x86_64-linux-gnu.so")
OPENVINO_PYTHON_SHA256 = "80939512e6bafefb3451f6a98731072662b971f299ce52460b2b22ad180032f1"
OPENVINO_CORE = Path("/opt/aster-news-video-xpu/ov-venv/lib/python3.12/site-packages/openvino/libs/libopenvino.so.2641")
OPENVINO_CORE_SHA256 = "9b9a80ac1f18e07b13ed54459d9a865bcfe9dc170dbf8fe740c2974b85ecedc1"
OPENVINO_GPU_PLUGIN = Path("/opt/aster-news-video-xpu/ov-venv/lib/python3.12/site-packages/openvino/libs/libopenvino_intel_gpu_plugin.so")
OPENVINO_GPU_PLUGIN_SHA256 = "e494cf8fb428f1fecfad35e2bac7b2fb24159ac6b13fe19027f0c4ae36374b33"
OPENCL_LOADER = Path("/opt/aster-news-video-xpu/venv/lib/libOpenCL.so.1")
OPENCL_LOADER_SHA256 = "8a27699968d48772bb7db64d5e69e5f34a8683d371cbb818e9e2033e46b70cf6"
INTEL_OPENCL_DRIVER = Path("/opt/aster-news-video-xpu/runtime/root/usr/lib/x86_64-linux-gnu/intel-opencl/libigdrcl.so")
INTEL_OPENCL_DRIVER_SHA256 = "4ac4495b787385a00c8655224ef534eb899b33cbf7e15ff1da39401c1b8f8b6d"
INTEL_GMM = Path("/opt/aster-news-video-xpu/runtime/root/usr/lib/x86_64-linux-gnu/libigdgmm.so.12")
INTEL_GMM_SHA256 = "41892701dc8de4a9086653e1599c533f40e8e28baf435df27cab70ec2d0b9526"
LEVEL_ZERO_LOADER = Path("/opt/aster-news-video-xpu/runtime/root/usr/lib/x86_64-linux-gnu/libze_loader.so.1")
LEVEL_ZERO_LOADER_SHA256 = "87743955768467949a57eb59df9218762e9e31588c784aa53b6a36314594b5c5"
INTEL_LEVEL_ZERO_DRIVER = Path("/opt/aster-news-video-xpu/runtime/root/usr/lib/x86_64-linux-gnu/libze_intel_gpu.so.1")
INTEL_LEVEL_ZERO_DRIVER_SHA256 = "b41a61e6da77e84b7557c90a67693f6b9f5f9d20a4bc8af301ad8bddbab6871e"


class RenderError(RuntimeError):
    pass


def pad(value: np.ndarray, size: int) -> np.ndarray:
    if value.shape[0] >= size:
        return value
    return np.concatenate((value, np.zeros((size - value.shape[0], *value.shape[1:]),
                                           dtype=value.dtype)))


def render(lease_id: str, generation: int) -> dict[str, object]:
    common.stage("VERIFY_PINS")
    common.verify()
    if (ov.__version__ != OPENVINO_VERSION
            or common.sha256(OPENVINO_PYTHON) != OPENVINO_PYTHON_SHA256
            or common.sha256(OPENVINO_CORE) != OPENVINO_CORE_SHA256
            or common.sha256(OPENVINO_GPU_PLUGIN) != OPENVINO_GPU_PLUGIN_SHA256
            or common.sha256(OPENCL_LOADER) != OPENCL_LOADER_SHA256
            or common.sha256(INTEL_OPENCL_DRIVER) != INTEL_OPENCL_DRIVER_SHA256
            or common.sha256(INTEL_GMM) != INTEL_GMM_SHA256
            or common.sha256(LEVEL_ZERO_LOADER) != LEVEL_ZERO_LOADER_SHA256
            or common.sha256(INTEL_LEVEL_ZERO_DRIVER) != INTEL_LEVEL_ZERO_DRIVER_SHA256):
        raise RenderError("OPENVINO_RUNTIME_DRIFT")
    if (common.sha256(IR_XML) != IR_XML_SHA256
            or common.sha256(IR_BIN) != IR_BIN_SHA256):
        raise RenderError("OPENVINO_IR_DRIFT")
    if os.environ.get("MUSETALK_DEVICE") != "cpu":
        raise RenderError("TORCH_CPU_NOT_FORCED")
    device_name = common.fixed_device_identity()

    common.stage("OPENVINO_COMPILE_GPU")
    core = ov.Core()
    compiled = core.compile_model(IR_XML, "GPU")
    try:
        device_name = str(core.get_property("GPU", "FULL_DEVICE_NAME"))
    except RuntimeError:
        pass

    sys.path.insert(0, str(common.SOURCE))
    from musetalk.models.vae import VAE
    from musetalk.utils.audio_processor import AudioProcessor
    from musetalk.utils.utils import datagen

    image = cv2.imread(str(common.INPUT_IMAGE), cv2.IMREAD_COLOR)
    if image is None:
        raise RenderError("INPUT_DECODE")
    x1, y1, x2, y2 = common.CROP
    crop = cv2.resize(image[y1:y2, x1:x2], (256, 256), interpolation=cv2.INTER_LANCZOS4)

    started = time.monotonic()
    with contextlib.redirect_stdout(sys.stderr):
        common.stage("LOAD_CPU_AUX_MODELS")
        vae = VAE(model_path=str(common.MODELS / "sd-vae"), use_float16=False)
        audio = AudioProcessor(feature_extractor_path=str(common.MODELS / "whisper"))
        whisper = WhisperModel.from_pretrained(str(common.MODELS / "whisper")).eval()
        whisper.requires_grad_(False)
        common.stage("AUDIO_FEATURES_CPU")
        features, sample_count = audio.get_audio_feature(str(common.INPUT_AUDIO))
        chunks = audio.get_whisper_chunk(
            features, torch.device("cpu"), torch.float32, whisper, sample_count,
            fps=common.FPS, audio_padding_length_left=2,
            audio_padding_length_right=2,
        )
        common.stage("VAE_LATENT_CPU")
        latent = vae.get_latents_for_unet(crop)
        generator = datagen(chunks, [latent], batch_size=common.BATCH_SIZE,
                            device=torch.device("cpu"))
        generated_frames: list[np.ndarray] = []
        common.stage("OPENVINO_INFERENCE_GPU")
        for whisper_batch, latent_batch in generator:
            audio_np = np.asarray(whisper_batch, dtype=np.float32)
            latent_np = latent_batch.detach().cpu().numpy().astype(np.float32)
            actual = audio_np.shape[0]
            result = compiled({
                "audio_feature": pad(audio_np, common.BATCH_SIZE),
                "video_feature": pad(latent_np, common.BATCH_SIZE),
                "timestep": np.array([0], dtype=np.int64),
            })[compiled.output(0)][:actual]
            generated_frames.extend(vae.decode_latents(torch.from_numpy(result)))

    common.stage("ENCODE_OUTPUT")
    safe_lease = re.sub(r"[^A-Za-z0-9_.-]", "-", lease_id)
    frame_dir = common.OUTPUTS / f"ov-frames-{safe_lease}-{generation}"
    frame_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    for index, generated in enumerate(generated_frames):
        output = common.blend_lower_face(image, generated)
        if not cv2.imwrite(str(frame_dir / f"{index:08d}.png"), output):
            raise RenderError("FRAME_WRITE")
    video_only = common.OUTPUTS / f"ov-video-{safe_lease}-{generation}.mp4"
    final = common.OUTPUTS / f"aster-musetalk-openvino-{safe_lease}-{generation}.mp4"
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    if subprocess.run((ffmpeg, "-y", "-v", "error", "-framerate", str(common.FPS),
                       "-i", str(frame_dir / "%08d.png"), "-c:v", "libx264",
                       "-pix_fmt", "yuv420p", "-crf", "18", str(video_only)),
                      timeout=300, check=False).returncode:
        raise RenderError("VIDEO_ENCODE")
    if subprocess.run((ffmpeg, "-y", "-v", "error", "-i", str(video_only), "-i",
                       str(common.INPUT_AUDIO), "-c:v", "copy", "-c:a", "aac",
                       "-shortest", str(final)), timeout=120, check=False).returncode:
        raise RenderError("AUDIO_MUX")
    return {
        "schema": "aster-news-video-musetalk-openvino-result.v1",
        "workload_id": WORKLOAD_ID, "lease_id": lease_id, "generation": generation,
        "source_commit": common.SOURCE_COMMIT, "source_tree": common.SOURCE_TREE,
        "openvino_version": OPENVINO_VERSION, "backend": "openvino:GPU",
        "device_name": device_name, "ir_xml_sha256": IR_XML_SHA256,
        "ir_bin_sha256": IR_BIN_SHA256, "fps": common.FPS,
        "batch_size": common.BATCH_SIZE, "frame_count": len(generated_frames),
        "render_seconds": round(time.monotonic() - started, 4),
        "output_path": str(final), "output_bytes": final.stat().st_size,
        "output_sha256": common.sha256(final), "network_used_during_render": False,
        "production_route_changed": False,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workload-id", required=True)
    parser.add_argument("--lease-id", required=True)
    parser.add_argument("--generation", required=True, type=int)
    args = parser.parse_args()
    try:
        if args.workload_id != WORKLOAD_ID or args.generation < 1:
            raise RenderError("WORKLOAD_IDENTITY")
        print(json.dumps(render(args.lease_id, args.generation), sort_keys=True), flush=True)
        return 0
    except BaseException as exc:
        code = (str(exc) if isinstance(exc, RenderError)
                else f"{type(exc).__name__}:{exc}")
        print(json.dumps({"code": re.sub(r"[^A-Za-z0-9_:-]", "_", code)[:120]}),
              file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
