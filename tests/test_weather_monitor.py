"""Tests for the Indiana weather monitor (offline: no network, no repo-root cache)."""

import json
import os

import indiana_weather_monitor as iwm


def test_module_imports():
    assert len(iwm.INDIANA_CITIES) == 92
    assert len(iwm.CITY_TO_COUNTY_MAPPING) == 92


def make_monitor(tmp_path):
    """Monitor whose cache file lives in tmp_path (isolated per test)."""
    m = iwm.IndianaWeatherMonitor()
    m.cache_file = str(tmp_path / "weather_cache.json")
    return m


def write_cache(path, payload):
    with open(path, "w") as f:
        json.dump(payload, f)


def test_load_cache_rejects_empty_weather_data(tmp_path):
    m = make_monitor(tmp_path)
    write_cache(m.cache_file, {"timestamp": "2026-09-21 10:00:00", "weather_data": {}})
    m.weather_data = {"stale": "keep"}
    assert m.load_cache() is False          # empty cache is not "valid data"
    assert m.data_fetched is False          # must not mark data as fetched


def test_load_cache_rejects_non_dict_body(tmp_path):
    m = make_monitor(tmp_path)
    with open(m.cache_file, "w") as f:
        f.write("null")                      # valid JSON, wrong shape
    assert m.load_cache() is False


def test_load_cache_survives_unreadable_file(tmp_path):
    m = make_monitor(tmp_path)
    write_cache(m.cache_file, {"weather_data": {"x": {}}})
    os.chmod(m.cache_file, 0)                # PermissionError path
    assert m.load_cache() is False           # must return False, not raise


def test_load_cache_survives_garbage_bytes(tmp_path):
    m = make_monitor(tmp_path)
    with open(m.cache_file, "wb") as f:
        f.write(b"\xff\xfe not json")        # UnicodeDecodeError path
    assert m.load_cache() is False


def test_load_cache_accepts_good_cache_and_stamps_it(tmp_path):
    m = make_monitor(tmp_path)
    write_cache(m.cache_file, {
        "timestamp": "2026-09-20 08:00:00",
        "weather_data": {"Peru": {"daily": {"temperature_2m_min": [40.0], "temperature_2m_max": [60.0], "time": ["2026-09-20"]}}},
    })
    assert m.load_cache() is True
    assert m.data_fetched is True
    assert m.data_timestamp == "2026-09-20 08:00:00"
    assert m.data_from_cache is True
    assert "Peru" in m.weather_data


def test_monitor_constructs_with_absolute_cache_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # cache path must NOT depend on cwd
    m = iwm.IndianaWeatherMonitor()
    assert m.cache_file.endswith("weather_cache.json")
    assert m.cache_file.startswith(os.path.dirname(iwm.__file__))