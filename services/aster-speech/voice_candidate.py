"""Repository-only M2 core for Aster's canonical Kokoro voice service.

The module deliberately contains no server or deployment wiring.  It defines
the shared text contract and bounded scheduler that HTTP and Wyoming adapters
will use after their independent protocol tests pass.
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from itertools import count
from typing import AsyncIterator, Callable, Literal, Sequence

from voice_metrics import VoiceMetrics

CallerClass = Literal["interactive", "batch"]
Renderer = Callable[[str], tuple[bytes, int]]

MAX_TEXT_CHARS = 2000
MAX_UNIT_CHARS = 240

_DOLLAR_AMOUNT = re.compile(
    r"(?<!\w)(?:(US|CA|AU)\s*)?\$(\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.(\d+))?(?:\s+(million|billion|trillion))?\b",
    re.IGNORECASE,
)
_ABBREVIATION_END = r"(?=(?:['’]s)?(?:\s|$|[-–—,;:!?]))"
_US_ABBREVIATION = re.compile(
    rf"\bU\.S(?:\.A)?\.{_ABBREVIATION_END}", re.IGNORECASE
)
_BC_ABBREVIATION = re.compile(
    rf"\bB\.C\.{_ABBREVIATION_END}", re.IGNORECASE
)
_LUTRON_CASETA = re.compile(r"\bLutron Cas[eé]ta\b", re.IGNORECASE)
_EMERGENCY_911 = re.compile(
    r"\b911\b(?=\s+(?:call|calls|caller|callers|dispatch|dispatcher|dispatchers|"
    r"operator|operators|service|services|emergency|centre|center)\b)",
    re.IGNORECASE,
)

_ONES = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
)
_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
_CURRENCY_NAMES = {"US": "United States", "CA": "Canadian", "AU": "Australian"}


def _under_thousand(number: int) -> str:
    if number < 20:
        return _ONES[number]
    if number < 100:
        tens, ones = divmod(number, 10)
        return _TENS[tens] + (f"-{_ONES[ones]}" if ones else "")
    hundreds, remainder = divmod(number, 100)
    return f"{_ONES[hundreds]} hundred" + (
        f" and {_under_thousand(remainder)}" if remainder else ""
    )


def _integer_words(number: int) -> str:
    if number < 1000:
        return _under_thousand(number)
    parts: list[str] = []
    for value, name in (
        (10**12, "trillion"), (10**9, "billion"),
        (10**6, "million"), (1000, "thousand"),
    ):
        chunk, number = divmod(number, value)
        if chunk:
            parts.append(f"{_under_thousand(chunk)} {name}")
    if number:
        return " ".join(parts) + (" and " if number < 100 else " ") + _under_thousand(number)
    return " ".join(parts)


def _spoken_currency(match: re.Match[str]) -> str:
    country = (match.group(1) or "").upper()
    whole = int(match.group(2).replace(",", ""))
    fraction = match.group(3)
    magnitude = match.group(4)
    prefix = f"{_CURRENCY_NAMES[country]} " if country else ""
    if magnitude:
        amount = _integer_words(whole)
        if fraction:
            amount += " point " + " ".join(_ONES[int(digit)] for digit in fraction)
        return f"{amount} {magnitude.lower()} {prefix}dollars"
    spoken = f"{_integer_words(whole)} {prefix}{'dollar' if whole == 1 and not fraction else 'dollars'}"
    if fraction:
        cents = int((fraction + "0")[:2])
        if cents:
            spoken += f" and {_integer_words(cents)} {'cent' if cents == 1 else 'cents'}"
    return spoken


def normalize_for_speech(text: str) -> str:
    """Return canonical engine input while retaining branded text upstream."""
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text).replace("*", "")
    text = re.sub(r"(?<!\w)_+(?!\w)", "", text)
    text = _US_ABBREVIATION.sub(
        lambda match: "United States" + ("." if match.end() == len(match.string) else ""), text
    )
    text = _BC_ABBREVIATION.sub(
        lambda match: "British Columbia" + ("." if match.end() == len(match.string) else ""), text
    )
    text = _EMERGENCY_911.sub("nine one one", text)
    text = _DOLLAR_AMOUNT.sub(_spoken_currency, text)
    text = text.replace("(", ", ").replace(")", ", ")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    text = re.sub(r",([.!?])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip(" ,")
    return _LUTRON_CASETA.sub("Lutron Caseta", text)


def semantic_units(text: str, maximum: int = MAX_UNIT_CHARS) -> list[str]:
    """Split normalized prose only at sentence/clause/word boundaries."""
    if maximum < 20:
        raise ValueError("maximum unit length is too small")
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    units: list[str] = []
    for sentence in sentences:
        pending = [sentence.strip()] if sentence.strip() else []
        while pending:
            part = pending.pop(0)
            if len(part) <= maximum:
                units.append(part)
                continue
            cut = max(part.rfind(mark, 0, maximum + 1) for mark in ("; ", ": ", ", ", " "))
            if cut < 1:
                cut = maximum
            units.append(part[:cut].rstrip(" ,;:"))
            pending.insert(0, part[cut:].lstrip(" ,;:"))
    return [unit for unit in units if unit]


@dataclass(frozen=True)
class AudioUnit:
    request_id: str
    index: int
    total: int
    pcm: bytes
    sample_rate: int


@dataclass
class _Job:
    request_id: str
    index: int
    total: int
    text: str
    result: asyncio.Future[AudioUnit]
    sequence: int = field(default=0)
    caller: CallerClass = "interactive"
    enqueued_at: float = field(default=0.0)


class VoiceScheduler:
    """Two interactive workers, with an optional isolated batch renderer."""

    def __init__(
        self,
        renderer: Renderer | Sequence[Renderer],
        interactive_capacity: int = 2,
        batch_capacity: int = 8,
        batch_renderer: Renderer | None = None,
        metrics: VoiceMetrics | None = None,
    ):
        if callable(renderer):
            self._renderers = (renderer, renderer)
        else:
            if len(renderer) != 2 or not all(callable(item) for item in renderer):
                raise ValueError("exactly two worker renderers are required")
            self._renderers = (renderer[0], renderer[1])
        self._interactive: asyncio.Queue[_Job] = asyncio.Queue(interactive_capacity)
        self._batch: asyncio.Queue[_Job] = asyncio.Queue(batch_capacity)
        self._batch_renderer = batch_renderer
        self._workers: list[asyncio.Task[None]] = []
        self._cancelled: set[str] = set()
        self._sequence = count()
        self.metrics = metrics or VoiceMetrics()

    async def start(self) -> None:
        if not self._workers:
            self._workers = [
                asyncio.create_task(self._worker(0)),
                asyncio.create_task(self._worker(1)),
            ]
            if self._batch_renderer is not None:
                self._workers.append(asyncio.create_task(self._batch_worker()))

    async def close(self) -> None:
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    def cancel(self, request_id: str, caller: CallerClass = "interactive") -> None:
        if request_id not in self._cancelled:
            self.metrics.cancellations[caller] += 1
            self._cancelled.add(request_id)

    def is_cancelled(self, request_id: str) -> bool:
        return request_id in self._cancelled

    async def stream(
        self, request_id: str, text: str, caller: CallerClass = "interactive"
    ) -> AsyncIterator[AudioUnit]:
        if not request_id:
            raise ValueError("request_id is required")
        if not text.strip():
            raise ValueError("text is required")
        if len(text) > MAX_TEXT_CHARS:
            raise ValueError("text exceeds the maximum permitted length")
        if request_id in self._cancelled:
            self._cancelled.remove(request_id)
        units = semantic_units(normalize_for_speech(text))
        loop = asyncio.get_running_loop()
        started = time.monotonic()
        outcome = "error"
        jobs = [
            _Job(request_id, index, len(units), unit, loop.create_future(),
                 next(self._sequence), caller, time.monotonic())
            for index, unit in enumerate(units)
        ]
        queue = self._interactive if caller == "interactive" else self._batch
        try:
            for job in jobs:
                await queue.put(job)
                self._update_queue_depths()
            for job in jobs:
                yield await job.result
            outcome = "ok"
        except asyncio.CancelledError:
            outcome = "cancelled"
            raise
        except Exception:
            outcome = "error"
            raise
        finally:
            if any(not job.result.done() for job in jobs):
                self.cancel(request_id, caller)
                outcome = "cancelled"
            self.metrics.observe_request(caller, outcome, time.monotonic() - started)

    async def _worker(self, worker_index: int) -> None:
        while True:
            job = await self._next_job(worker_index)
            self._update_queue_depths()
            if job.request_id in self._cancelled:
                if not job.result.done():
                    job.result.cancel()
                continue
            try:
                self.metrics.observe_queue(job.caller, time.monotonic() - job.enqueued_at)
                self.metrics.workers_busy["interactive"] += 1
                pcm, sample_rate = await asyncio.to_thread(
                    self._renderers[worker_index], job.text
                )
                if job.request_id in self._cancelled:
                    job.result.cancel()
                elif not job.result.done():
                    job.result.set_result(
                        AudioUnit(job.request_id, job.index, job.total, pcm, sample_rate)
                    )
            except Exception as exc:
                self.metrics.render_errors[job.caller] += 1
                if not job.result.done():
                    job.result.set_exception(exc)
            finally:
                self.metrics.workers_busy["interactive"] -= 1

    async def _batch_worker(self) -> None:
        """Render batch work outside both latency-sensitive workers."""
        assert self._batch_renderer is not None
        while True:
            job = await self._batch.get()
            self._update_queue_depths()
            if job.request_id in self._cancelled:
                if not job.result.done():
                    job.result.cancel()
                continue
            try:
                self.metrics.observe_queue("batch", time.monotonic() - job.enqueued_at)
                self.metrics.workers_busy["batch"] += 1
                pcm, sample_rate = await asyncio.to_thread(self._batch_renderer, job.text)
                if job.request_id in self._cancelled:
                    job.result.cancel()
                elif not job.result.done():
                    job.result.set_result(
                        AudioUnit(job.request_id, job.index, job.total, pcm, sample_rate)
                    )
            except Exception as exc:
                self.metrics.render_errors["batch"] += 1
                if not job.result.done():
                    job.result.set_exception(exc)
            finally:
                self.metrics.workers_busy["batch"] -= 1

    def _update_queue_depths(self) -> None:
        self.metrics.queue_depth["interactive"] = self._interactive.qsize()
        self.metrics.queue_depth["batch"] = self._batch.qsize()

    async def _next_job(self, worker_index: int) -> _Job:
        if worker_index == 1 or self._batch_renderer is not None:
            return await self._interactive.get()
        try:
            return self._interactive.get_nowait()
        except asyncio.QueueEmpty:
            interactive = asyncio.create_task(self._interactive.get())
            batch = asyncio.create_task(self._batch.get())
            try:
                done, _pending = await asyncio.wait(
                    (interactive, batch), return_when=asyncio.FIRST_COMPLETED
                )
            except asyncio.CancelledError:
                interactive.cancel()
                batch.cancel()
                await asyncio.gather(interactive, batch, return_exceptions=True)
                raise
            if interactive in done:
                if batch.done():
                    self._batch.put_nowait(batch.result())
                else:
                    batch.cancel()
                    await asyncio.gather(batch, return_exceptions=True)
                return interactive.result()
            interactive.cancel()
            await asyncio.gather(interactive, return_exceptions=True)
            return batch.result()
