"""Trusted wall-clock/monotonic owner wrapper for the full-drain candidate."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from full_inference_lab_session import FullInferenceDrainController, FullDrainError


@dataclass
class TrustedDrainOwner:
    owner_id: str
    wall_clock: Callable[[], float] = time.time
    monotonic: Callable[[], float] = time.monotonic
    _last_monotonic: float | None = None

    def assert_present(self) -> None:
        if not self.owner_id:
            raise FullDrainError("owner identity is empty")
        current = self.monotonic()
        if self._last_monotonic is not None and current < self._last_monotonic:
            raise FullDrainError("trusted monotonic clock moved backwards")
        self._last_monotonic = current

    def now_epoch(self) -> int:
        self.assert_present()
        return int(self.wall_clock())

    def heartbeat(self, controller: FullInferenceDrainController) -> None:
        controller.heartbeat(self.now_epoch())

    def require_work_window(self, controller: FullInferenceDrainController) -> None:
        controller.require_work_window(self.now_epoch())
