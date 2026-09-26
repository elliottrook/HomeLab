#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("b60_kernel_log", HERE / "kernel_log.py")
assert SPEC and SPEC.loader
kernel_log = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kernel_log)


class KernelLogTests(unittest.TestCase):
    def test_clean_relevant_excerpt_is_accepted(self):
        text = (HERE / "fixtures/kernel-log-clean.txt").read_text(encoding="utf-8")
        self.assertEqual(kernel_log.classify(kernel_log.sanitize(text)), [])

    def test_reset_oom_loss_and_hang_are_classified(self):
        text = "\n".join((
            "kernel: xe GPU reset completed",
            "kernel: Out of memory in drm worker",
            "kernel: xe device was lost",
            "kernel: drm engine hang detected",
        ))
        self.assertEqual(kernel_log.classify(kernel_log.sanitize(text)),
                         ["kernel_oom", "gpu_reset", "device_loss", "gpu_hang"])

    def test_irrelevant_secret_and_oversize_input_are_rejected(self):
        for text in ("kernel: ordinary message\n", "kernel: xe token=not-safe\n",
                     "kernel: xe\n" * 501):
            with self.assertRaises(kernel_log.KernelLogError):
                kernel_log.sanitize(text)
