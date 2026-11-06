#!/opt/aster-news-video-xpu/ov-venv/bin/python
"""Convert the pinned MuseTalk 1.5 positional encoder and UNet to OpenVINO IR."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

import openvino as ov
import torch


ROOT = Path("/opt/aster-news-video-xpu")
SOURCE = ROOT / "source/MuseTalk"
MODELS = ROOT / "models"
OUTPUT = MODELS / "openvino/musetalk-v15-unet-pe-b4.xml"
UNET = MODELS / "musetalkV15/unet.pth"
CONFIG = MODELS / "musetalkV15/musetalk.json"
UNET_SHA256 = "7ebf6c98c181e20838e4c0054e96e944ac60d5d692cc01db42839fe11b787007"
CONFIG_SHA256 = "5b6923aee04d71692e0e9846c471e0a4ea07a4f686d39545e472bd4ba17e1b47"
BATCH_SIZE = 4


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class UnetWithPositionalEncoding(torch.nn.Module):
    def __init__(self, model: torch.nn.Module, positional_encoding: torch.nn.Module):
        super().__init__()
        self.model = model
        self.positional_encoding = positional_encoding

    def forward(self, audio_feature: torch.Tensor, video_feature: torch.Tensor,
                timestep: torch.Tensor) -> torch.Tensor:
        encoded = self.positional_encoding(audio_feature)
        return self.model(video_feature, timestep,
                          encoder_hidden_states=encoded).sample


def main() -> int:
    if os.environ.get("MUSETALK_DEVICE") != "cpu":
        raise RuntimeError("conversion must be CPU-only")
    if sha256(UNET) != UNET_SHA256 or sha256(CONFIG) != CONFIG_SHA256:
        raise RuntimeError("pinned MuseTalk inputs drifted")
    sys.path.insert(0, str(SOURCE))
    from musetalk.models.unet import UNet

    unet = UNet(str(CONFIG), str(UNET), device=torch.device("cpu"))
    wrapper = UnetWithPositionalEncoding(unet.model.eval(), unet.pe.eval()).eval()
    example = (
        torch.zeros(BATCH_SIZE, 50, 384, dtype=torch.float32),
        torch.zeros(BATCH_SIZE, 8, 32, 32, dtype=torch.float32),
        torch.tensor([0], dtype=torch.int64),
    )
    model = ov.convert_model(wrapper, example_input=example)
    OUTPUT.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    ov.save_model(model, OUTPUT, compress_to_fp16=True)
    binary = OUTPUT.with_suffix(".bin")
    result = {
        "schema": "aster-news-video-musetalk-openvino-ir.v1",
        "openvino_version": ov.__version__,
        "batch_size": BATCH_SIZE,
        "xml_path": str(OUTPUT),
        "xml_sha256": sha256(OUTPUT),
        "bin_path": str(binary),
        "bin_sha256": sha256(binary),
        "unet_sha256": UNET_SHA256,
        "config_sha256": CONFIG_SHA256,
    }
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
