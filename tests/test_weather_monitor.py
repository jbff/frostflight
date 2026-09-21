"""Tests for the Indiana weather monitor (offline: no network, no repo-root cache)."""

import indiana_weather_monitor as iwm


def test_module_imports():
    assert len(iwm.INDIANA_CITIES) == 92
    assert len(iwm.CITY_TO_COUNTY_MAPPING) == 92
