"""Testes do módulo de métricas de observabilidade."""

from __future__ import annotations

import pytest

from inpe_bdc_mcp.utils.metrics import APIMetrics


class TestAPIMetrics:
    def test_track_records_call_and_latency(self):
        m = APIMetrics()
        with m.track("test_op"):
            pass
        snap = m.snapshot()
        assert "test_op" in snap
        assert snap["test_op"]["calls"] == 1
        assert snap["test_op"]["errors"] == 0
        assert snap["test_op"]["total_ms"] >= 0

    def test_track_records_errors(self):
        m = APIMetrics()
        with pytest.raises(ValueError):
            with m.track("fail_op"):
                raise ValueError("teste")
        snap = m.snapshot()
        assert snap["fail_op"]["calls"] == 1
        assert snap["fail_op"]["errors"] == 1

    def test_multiple_calls_accumulate(self):
        m = APIMetrics()
        for _ in range(5):
            with m.track("multi"):
                pass
        snap = m.snapshot()
        assert snap["multi"]["calls"] == 5
        assert snap["multi"]["avg_ms"] >= 0

    def test_reset_clears_all(self):
        m = APIMetrics()
        with m.track("op"):
            pass
        m.reset()
        assert m.snapshot() == {}

    def test_snapshot_empty(self):
        m = APIMetrics()
        assert m.snapshot() == {}
