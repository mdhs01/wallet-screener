import os

import pytest

from src.wallet_screener.configuration import ConfigurationError, RuntimeSettings
from src.wallet_screener.config import ScreenerConfig


def test_defaults(monkeypatch):
    for key in (
        "WALLET_SCREENER_PROVIDER",
        "WALLET_SCREENER_MAX_CANDIDATES",
        "WALLET_SCREENER_INTERVAL_SECONDS",
        "WALLET_SCREENER_DB",
        "GMGN_CLI_PATH",
        "GMGN_CHAIN",
        "GMGN_CLI_TIMEOUT",
        "GMGN_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    settings = RuntimeSettings.from_env()
    assert settings.provider == "null"
    assert settings.max_candidates == 50
    assert settings.schedule_interval_seconds == 300.0
    assert settings.gmgn_api_key is None


def test_numeric_validation(monkeypatch):
    monkeypatch.setenv("WALLET_SCREENER_MAX_CANDIDATES", "bad")
    with pytest.raises(ConfigurationError):
        RuntimeSettings.from_env()


def test_provider_validation(monkeypatch):
    monkeypatch.setenv("WALLET_SCREENER_PROVIDER", "unknown")
    settings = RuntimeSettings.from_env()
    with pytest.raises(ConfigurationError):
        settings.validate()


def test_surface_calibration_defaults():
    config = ScreenerConfig()
    assert config.surface.min_pnl_ratio == 0.20
    assert config.surface.max_tx_7d == 750
    assert config.surface.normal_tx_7d_max == 300
    assert config.surface.active_tx_7d_max == 500
