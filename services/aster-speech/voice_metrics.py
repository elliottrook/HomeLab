"""Dependency-free, low-cardinality Prometheus metrics for Aster Voice."""

from __future__ import annotations

from collections import Counter


BUCKETS = (0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.5, 5.0, 10.0, 30.0, 60.0)


class VoiceMetrics:
    def __init__(self) -> None:
        self.requests: Counter[tuple[str, str]] = Counter()
        self.render_errors: Counter[str] = Counter()
        self.cancellations: Counter[str] = Counter()
        self.request_seconds: dict[str, list[float]] = {"interactive": [], "batch": []}
        self.queue_seconds: dict[str, list[float]] = {"interactive": [], "batch": []}
        self.queue_depth = {"interactive": 0, "batch": 0}
        self.workers_busy = {"interactive": 0, "batch": 0}

    def observe_request(self, caller: str, outcome: str, seconds: float) -> None:
        self.requests[(caller, outcome)] += 1
        self.request_seconds[caller].append(max(0.0, seconds))

    def observe_queue(self, caller: str, seconds: float) -> None:
        self.queue_seconds[caller].append(max(0.0, seconds))

    def render(self) -> str:
        lines = [
            "# HELP aster_voice_requests_total Completed voice requests.",
            "# TYPE aster_voice_requests_total counter",
        ]
        for caller in ("interactive", "batch"):
            for outcome in ("ok", "cancelled", "error"):
                lines.append(
                    f'aster_voice_requests_total{{caller="{caller}",outcome="{outcome}"}} '
                    f'{self.requests[(caller, outcome)]}'
                )
        lines.extend(self._histogram("aster_voice_request_duration_seconds", self.request_seconds))
        lines.extend(self._histogram("aster_voice_queue_wait_seconds", self.queue_seconds))
        lines.extend([
            "# HELP aster_voice_queue_depth Current queued synthesis units.",
            "# TYPE aster_voice_queue_depth gauge",
            *[f'aster_voice_queue_depth{{caller="{caller}"}} {self.queue_depth[caller]}'
              for caller in ("interactive", "batch")],
            "# HELP aster_voice_workers_busy Current rendering workers.",
            "# TYPE aster_voice_workers_busy gauge",
            *[f'aster_voice_workers_busy{{caller="{caller}"}} {self.workers_busy[caller]}'
              for caller in ("interactive", "batch")],
            "# HELP aster_voice_render_errors_total Renderer failures.",
            "# TYPE aster_voice_render_errors_total counter",
            *[f'aster_voice_render_errors_total{{caller="{caller}"}} {self.render_errors[caller]}'
              for caller in ("interactive", "batch")],
            "# HELP aster_voice_cancellations_total Cancelled voice requests.",
            "# TYPE aster_voice_cancellations_total counter",
            *[f'aster_voice_cancellations_total{{caller="{caller}"}} {self.cancellations[caller]}'
              for caller in ("interactive", "batch")],
        ])
        return "\n".join(lines) + "\n"

    @staticmethod
    def _histogram(name: str, values_by_caller: dict[str, list[float]]) -> list[str]:
        lines = [f"# TYPE {name} histogram"]
        for caller in ("interactive", "batch"):
            values = values_by_caller[caller]
            for boundary in BUCKETS:
                count = sum(value <= boundary for value in values)
                lines.append(f'{name}_bucket{{caller="{caller}",le="{boundary}"}} {count}')
            lines.append(f'{name}_bucket{{caller="{caller}",le="+Inf"}} {len(values)}')
            lines.append(f'{name}_sum{{caller="{caller}"}} {sum(values):.6f}')
            lines.append(f'{name}_count{{caller="{caller}"}} {len(values)}')
        return lines
