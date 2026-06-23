"""Observability Service - Tracks tokens, latency, fallback, confidence metrics."""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MetricEntry:
    timestamp: float
    event_type: str
    tokens_estimated: int = 0
    latency_ms: float = 0.0
    fallback_used: bool = False
    confidence: Optional[float] = None
    human_confirm_needed: bool = False
    notes: str = ""


class ObservabilityTracker:
    def __init__(self):
        self.metrics: list[MetricEntry] = []
        self._timer_start: Optional[float] = None

    def start_timer(self):
        self._timer_start = time.time()

    def stop_timer(self) -> float:
        if self._timer_start is None:
            return 0.0
        elapsed = (time.time() - self._timer_start) * 1000
        self._timer_start = None
        return elapsed

    def record(self, event_type: str, tokens: int = 0, latency_ms: float = 0.0,
               fallback: bool = False, confidence: Optional[float] = None,
               human_confirm: bool = False, notes: str = "") -> None:
        self.metrics.append(MetricEntry(
            timestamp=time.time(),
            event_type=event_type,
            tokens_estimated=tokens,
            latency_ms=latency_ms,
            fallback_used=fallback,
            confidence=confidence,
            human_confirm_needed=human_confirm,
            notes=notes,
        ))

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation: ~4 chars per token for English, ~2 for CJK."""
        return max(1, len(text) // 4)

    def get_summary(self) -> dict:
        if not self.metrics:
            return {"total_events": 0}

        total_tokens = sum(m.tokens_estimated for m in self.metrics)
        avg_latency = sum(m.latency_ms for m in self.metrics) / len(self.metrics)
        fallback_count = sum(1 for m in self.metrics if m.fallback_used)
        confidences = [m.confidence for m in self.metrics if m.confidence is not None]
        low_confidence_count = sum(1 for c in confidences if c < 0.6)
        human_confirms = sum(1 for m in self.metrics if m.human_confirm_needed)

        return {
            "total_events": len(self.metrics),
            "total_tokens_estimated": total_tokens,
            "avg_latency_ms": round(avg_latency, 1),
            "fallback_count": fallback_count,
            "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else None,
            "low_confidence_count": low_confidence_count,
            "low_confidence_rate": round(low_confidence_count / len(confidences), 3) if confidences else 0,
            "human_confirm_count": human_confirms,
        }

    def get_alerts(self) -> list[dict]:
        """Detect anomalies: token spikes, consecutive fallbacks, high low-confidence rate."""
        alerts = []
        summary = self.get_summary()

        # Consecutive fallbacks
        consecutive_fb = 0
        max_consecutive_fb = 0
        for m in self.metrics:
            if m.fallback_used:
                consecutive_fb += 1
                max_consecutive_fb = max(max_consecutive_fb, consecutive_fb)
            else:
                consecutive_fb = 0
        if max_consecutive_fb >= 2:
            alerts.append({
                "type": "consecutive_fallback",
                "severity": "warning",
                "message": f"Consecutive fallbacks detected: {max_consecutive_fb} in a row",
            })

        # Low confidence rate too high
        if summary.get("low_confidence_rate", 0) > 0.3:
            alerts.append({
                "type": "low_confidence_rate",
                "severity": "warning",
                "message": f"Low confidence rate: {summary['low_confidence_rate']:.1%}",
            })

        # Token spike (any single event > 2x average)
        if summary["total_events"] > 1:
            avg_tokens = summary["total_tokens_estimated"] / summary["total_events"]
            for m in self.metrics:
                if m.tokens_estimated > avg_tokens * 2 and avg_tokens > 50:
                    alerts.append({
                        "type": "token_spike",
                        "severity": "info",
                        "message": f"Token spike in {m.event_type}: {m.tokens_estimated} tokens (avg: {avg_tokens:.0f})",
                    })
                    break

        return alerts

    def reset(self):
        self.metrics = []


# Singleton
tracker = ObservabilityTracker()
