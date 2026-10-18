"""Offline plan generator for a cooperative daytime B60 lab reservation."""

from __future__ import annotations

from dataclasses import dataclass

from application_b60_controller import ApplicationPreLease
from application_b60_lease import ACCEPTED_BACKEND, APPLICATION_MODE

MAX_LAB_SECONDS = 45 * 60
MIN_RESTORE_RESERVE_SECONDS = 15 * 60
NEWS_CONSUMER = ("114", "news-aggregator")
STOP_CONSUMERS = (("104", "aster-agent.service"),
                  ("116", "aster-speech.service"),
                  ("114", "news-aggregator-ingest.timer"),
                  ("114", "news-aggregator-digest.timer"))


class LabSessionError(ValueError):
    pass


@dataclass(frozen=True)
class LabRuntimePreflight:
    backend_identity: str
    gpu_visible: bool
    authentication_verified: bool
    source_verified: bool
    news_timers_active: bool


@dataclass(frozen=True)
class LabSessionPlan:
    mode: str
    lease_id: str
    generation: int
    lab_seconds: int
    restore_reserve_seconds: int
    preserve_backend: bool
    stop_commands: tuple[tuple[str, ...], ...]
    restore_commands: tuple[tuple[str, ...], ...]


def _command(vmid: str, *args: str) -> tuple[str, ...]:
    return ("pct", "exec", vmid, "--", *args)


def plan(prelease: ApplicationPreLease, runtime: LabRuntimePreflight,
         *, lab_seconds: int = MAX_LAB_SECONDS) -> LabSessionPlan:
    """Create a fixed cooperative plan; never executes a command."""
    if (prelease.mode != APPLICATION_MODE or not prelease.lease_id
            or type(prelease.generation) is not int or prelease.generation < 1):
        raise LabSessionError("application lab lease identity is invalid")
    if (runtime.backend_identity != ACCEPTED_BACKEND or not runtime.gpu_visible
            or not runtime.authentication_verified or not runtime.source_verified
            or not runtime.news_timers_active):
        raise LabSessionError("runtime source preflight is incomplete")
    if (not prelease.llama_service_active or not prelease.consumers_healthy
            or not prelease.news_quiesced):
        raise LabSessionError("consumer preflight is incomplete")
    if type(lab_seconds) is not int or not 1 <= lab_seconds <= MAX_LAB_SECONDS:
        raise LabSessionError("daytime lab budget is outside its bound")
    if (prelease.restore_deadline_epoch - prelease.restore_start_epoch
            < MIN_RESTORE_RESERVE_SECONDS):
        raise LabSessionError("restoration reserve is insufficient")
    return LabSessionPlan(
        mode="cooperative-lab-v1", lease_id=prelease.lease_id,
        generation=prelease.generation, lab_seconds=lab_seconds,
        restore_reserve_seconds=MIN_RESTORE_RESERVE_SECONDS,
        preserve_backend=True,
        stop_commands=(
            _command("104", "systemctl", "stop", "aster-agent.service"),
            _command("116", "systemctl", "stop", "aster-speech.service"),
            _command("114", "systemctl", "stop", "news-aggregator-ingest.timer"),
            _command("114", "systemctl", "stop", "news-aggregator-digest.timer")),
        restore_commands=(
            _command("114", "systemctl", "start", "news-aggregator-digest.timer"),
            _command("114", "systemctl", "start", "news-aggregator-ingest.timer"),
            _command("116", "systemctl", "start", "aster-speech.service"),
            _command("104", "systemctl", "start", "aster-agent.service")))
