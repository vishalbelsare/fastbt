"""
Tests for fastbt.backtest.data — DataSource protocol and DuckDBParquetLoader.
Run with: uv run pytest tests/backtest/test_data.py -v
"""

import math
import os
import inspect

import duckdb
import pandas as pd
import pytest

from fastbt.backtest.data import DataSource, DuckDBParquetLoader, DuckDBVortexLoader

REAL_DATA = os.path.expandvars("$HOME/data/q1_2025.parquet")


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def parquet_path(tmp_path_factory):
    """
    Minimal parquet matching the real q1_2025 schema:
    underlying_price is embedded in each option row (no separate underlying rows).
    """
    tmp = tmp_path_factory.mktemp("data")
    path = tmp / "test.parquet"

    rows = []
    for date in ["2025-01-02", "2025-01-03"]:
        for time in ["09:15:00", "09:16:00", "09:17:00", "15:29:00"]:
            for strike, opt in [(23400, "CE"), (23400, "PE"), (23450, "CE")]:
                rows.append(
                    {
                        "trade_date": date,
                        "trade_time": time,
                        "underlying_price": 23400.0,
                        "strike": strike,
                        "option_type": opt,
                        "expiry": "2025-01-30",
                        "open": 100.0,
                        "high": 105.0,
                        "low": 98.0,
                        "close": 102.0,
                        "volume": 500.0,
                    }
                )
    pd.DataFrame(rows).to_parquet(path, index=False)
    return str(path)


@pytest.fixture(scope="module")
def loader(parquet_path):
    return DuckDBParquetLoader(parquet_path)


# ─── DataSource protocol ──────────────────────────────────────────────────────


class TestDataSourceProtocol:
    def test_is_abstract(self):
        """DataSource cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DataSource()  # type: ignore

    def test_get_instrument_data_has_no_start_time(self):
        """Phase 1 decision: full-day fetch — no start_time filter allowed."""
        sig = inspect.signature(DataSource.get_instrument_data)
        assert "start_time" not in sig.parameters

    def test_duckdb_loader_is_concrete(self, loader):
        """DuckDBParquetLoader must implement all abstract methods."""
        assert isinstance(loader, DataSource)


# ─── get_underlying_data ─────────────────────────────────────────────────────


class TestGetUnderlyingData:
    def test_returns_dict(self, loader):
        result = loader.get_underlying_data("2025-01-02")
        assert isinstance(result, dict)

    def test_keys_are_strings(self, loader):
        result = loader.get_underlying_data("2025-01-02")
        assert all(isinstance(k, str) for k in result.keys())

    def test_values_are_floats(self, loader):
        result = loader.get_underlying_data("2025-01-02")
        assert all(isinstance(v, float) for v in result.values())

    def test_all_ticks_present(self, loader):
        """4 distinct time ticks in the fixture."""
        result = loader.get_underlying_data("2025-01-02")
        assert len(result) == 4

    def test_sorted_by_time(self, loader):
        result = loader.get_underlying_data("2025-01-02")
        keys = list(result.keys())
        assert keys == sorted(keys)

    def test_bad_date_returns_empty(self, loader):
        result = loader.get_underlying_data("2099-01-01")
        assert result == {}


# ─── get_instrument_data ──────────────────────────────────────────────────────


class TestGetInstrumentData:
    def test_returns_nested_dict(self, loader):
        result = loader.get_instrument_data("2025-01-02", 23400, "CE")
        assert isinstance(result, dict)
        first_val = next(iter(result.values()))
        assert isinstance(first_val, dict)

    def test_ohlcv_keys_present(self, loader):
        result = loader.get_instrument_data("2025-01-02", 23400, "CE")
        bar = next(iter(result.values()))
        assert {"open", "high", "low", "close", "volume"}.issubset(bar.keys())

    def test_full_day_all_ticks_present(self, loader):
        """Full-day fetch — all 4 time ticks must be present, no filtering."""
        result = loader.get_instrument_data("2025-01-02", 23400, "CE")
        assert len(result) == 4

    def test_earliest_tick_present(self, loader):
        """09:15 must be in cache — proves no start_time filter being applied."""
        result = loader.get_instrument_data("2025-01-02", 23400, "CE")
        assert "09:15:00" in result

    def test_values_are_floats(self, loader):
        result = loader.get_instrument_data("2025-01-02", 23400, "CE")
        bar = next(iter(result.values()))
        assert all(isinstance(v, float) for v in bar.values())

    def test_bad_strike_returns_empty(self, loader):
        result = loader.get_instrument_data("2025-01-02", 99999, "CE")
        assert result == {}

    def test_bad_date_returns_empty(self, loader):
        result = loader.get_instrument_data("2099-01-01", 23400, "CE")
        assert result == {}

    def test_pe_option(self, loader):
        result = loader.get_instrument_data("2025-01-02", 23400, "PE")
        assert len(result) == 4


# ─── get_instrument_data: NULL / non-numeric extra columns (issue #16) ────────


def _vortex_available() -> bool:
    try:
        duckdb.connect().execute("INSTALL vortex; LOAD vortex;")
        return True
    except Exception:
        return False


@pytest.fixture(scope="module", params=["parquet", "vortex"])
def mixed_loader(request, tmp_path_factory):
    """
    Loader over a file whose extra columns hold a NULL greek, a DECIMAL and a
    VARCHAR expiry — the three cases that used to raise in float().
    """
    fmt = request.param
    if fmt == "vortex" and not _vortex_available():
        pytest.skip("DuckDB vortex extension not available")

    path = tmp_path_factory.mktemp("mixed") / f"mixed.{fmt}"
    con = duckdb.connect()
    if fmt == "vortex":
        con.execute("LOAD vortex")
    con.execute(
        f"""
        COPY (
            SELECT * FROM (VALUES
                ('2025-01-02', '09:15:00', 23400, 'CE', 100.0, 105.0, 98.0, 102.0, 500.0,
                 0.52::DOUBLE, 1.25::DECIMAL(10, 2), '2025-01-30 00:00:00'),
                ('2025-01-02', '09:16:00', 23400, 'CE', 101.0, 106.0, 99.0, 103.0, 400.0,
                 NULL::DOUBLE, 1.50::DECIMAL(10, 2), '2025-01-30 00:00:00')
            ) t(trade_date, trade_time, strike, option_type, open, high, low, close,
                volume, delta, iv, expiry)
        ) TO '{path}' (FORMAT {fmt})
        """
    )
    extra = ["delta", "iv", "expiry"]
    if fmt == "vortex":
        return DuckDBVortexLoader(str(path), extra_columns=extra)
    return DuckDBParquetLoader(str(path), extra_columns=extra)


class TestGetInstrumentDataMixedColumns:
    def test_does_not_raise_and_keeps_all_bars(self, mixed_loader):
        result = mixed_loader.get_instrument_data("2025-01-02", 23400, "CE")
        assert list(result) == ["09:15:00", "09:16:00"]

    def test_null_becomes_nan(self, mixed_loader):
        result = mixed_loader.get_instrument_data("2025-01-02", 23400, "CE")
        assert math.isnan(result["09:16:00"]["delta"])
        assert result["09:15:00"]["delta"] == pytest.approx(0.52)

    def test_null_greek_fails_closed_in_comparisons(self, mixed_loader):
        result = mixed_loader.get_instrument_data("2025-01-02", 23400, "CE")
        delta = result["09:16:00"]["delta"]
        assert not (delta > 0.3) and not (delta < 0.3)

    def test_decimal_becomes_float(self, mixed_loader):
        bar = mixed_loader.get_instrument_data("2025-01-02", 23400, "CE")["09:15:00"]
        assert type(bar["iv"]) is float
        assert bar["iv"] == pytest.approx(1.25)

    def test_varchar_kept_as_str(self, mixed_loader):
        bar = mixed_loader.get_instrument_data("2025-01-02", 23400, "CE")["09:15:00"]
        assert bar["expiry"] == "2025-01-30 00:00:00"

    def test_ohlcv_are_floats(self, mixed_loader):
        bar = mixed_loader.get_instrument_data("2025-01-02", 23400, "CE")["09:16:00"]
        for col in ("open", "high", "low", "close", "volume"):
            assert type(bar[col]) is float


# ─── get_available_dates ─────────────────────────────────────────────────────


class TestGetAvailableDates:
    def test_returns_list_of_strings(self, loader):
        result = loader.get_available_dates()
        assert isinstance(result, list)
        assert all(isinstance(d, str) for d in result)

    def test_contains_fixture_dates(self, loader):
        result = loader.get_available_dates()
        assert "2025-01-02" in result
        assert "2025-01-03" in result

    def test_sorted(self, loader):
        result = loader.get_available_dates()
        assert result == sorted(result)


# ─── Static helpers ───────────────────────────────────────────────────────────


class TestStaticHelpers:
    def test_atm_exact(self):
        assert DuckDBParquetLoader.get_atm_strike(23400.0, step=50) == 23400

    def test_atm_rounds_up(self):
        assert DuckDBParquetLoader.get_atm_strike(23438.0, step=50) == 23450

    def test_atm_rounds_down(self):
        assert DuckDBParquetLoader.get_atm_strike(23412.0, step=50) == 23400

    def test_get_strike_zero_distance(self):
        assert DuckDBParquetLoader.get_strike(23400.0, step=50, distance=0) == 23400

    def test_get_strike_positive(self):
        assert DuckDBParquetLoader.get_strike(23400.0, step=50, distance=2) == 23500

    def test_get_strike_negative(self):
        assert DuckDBParquetLoader.get_strike(23400.0, step=50, distance=-1) == 23350


# ─── Real-data integration (optional) ────────────────────────────────────────


class TestRealDataIntegration:
    """Runs only if $HOME/data/q1_2025.parquet exists."""

    def _skip_if_no_real_data(self):
        if not os.path.exists(REAL_DATA):
            pytest.skip("Real data not available")

    def test_real_available_dates(self):
        self._skip_if_no_real_data()
        loader = DuckDBParquetLoader(REAL_DATA)
        dates = loader.get_available_dates()
        assert len(dates) > 0
        assert all(len(d) == 10 for d in dates)  # "YYYY-MM-DD"

    def test_real_underlying_data(self):
        self._skip_if_no_real_data()
        loader = DuckDBParquetLoader(REAL_DATA)
        dates = loader.get_available_dates()
        result = loader.get_underlying_data(dates[0])
        assert len(result) > 0
        assert all(isinstance(v, float) for v in result.values())
        # Earliest tick must be 09:15
        first_tick = next(iter(result))
        assert first_tick.startswith("09:15")

    def test_real_instrument_full_day(self):
        """Full-day fetch returns data from 09:15, not just from entry time."""
        self._skip_if_no_real_data()
        loader = DuckDBParquetLoader(REAL_DATA)
        dates = loader.get_available_dates()
        spot = list(loader.get_underlying_data(dates[0]).values())[0]
        atm = DuckDBParquetLoader.get_atm_strike(spot, step=50)
        result = loader.get_instrument_data(dates[0], atm, "CE")
        assert len(result) > 0
        first_tick = next(iter(result))
        assert first_tick.startswith(
            "09:15"
        ), f"Expected full-day data starting 09:15, got {first_tick}"
        assert len(result) > 0
        first_tick = next(iter(result))
        assert first_tick.startswith(
            "09:15"
        ), f"Expected full-day data starting 09:15, got {first_tick}"
