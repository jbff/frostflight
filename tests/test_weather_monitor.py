"""Tests for the Indiana weather monitor (offline: no network, no repo-root cache)."""

import json
import os
import pytest
from datetime import datetime, timedelta

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
        "weather_data": {"Peru": {"current_weather": {"temperature": 55.0}, "daily": {"temperature_2m_min": [40.0], "temperature_2m_max": [60.0], "time": ["2026-09-20"]}}},
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


def make_payload(min_temp=40.0):
    """Minimal well-formed Open-Meteo payload."""
    return {
        "current_weather": {"temperature": 55.0, "windspeed": 5.0, "time": "2026-09-21T08:00"},
        "daily": {
            "temperature_2m_min": [min_temp, 38.0],
            "temperature_2m_max": [70.0, 65.0],
            "time": ["2026-09-21", "2026-09-22"],
        },
    }


def test_failed_fetch_not_cached_or_marked_fetched(tmp_path, monkeypatch):
    m = make_monitor(tmp_path)
    monkeypatch.setattr(m, "get_weather_data", lambda city, coords: None)
    m.fetch_all_weather_data()
    assert m.data_fetched is False
    assert m.weather_data == {}
    import os
    assert not os.path.exists(m.cache_file)  # nothing cached from a total failure


def test_failure_sweep_not_repeated_per_consumer(tmp_path, monkeypatch):
    m = make_monitor(tmp_path)
    calls = []

    def counting_fail(city, coords):
        calls.append(city)
        return None

    monkeypatch.setattr(m, "get_weather_data", counting_fail)
    m.get_county_temperature_data()
    m.analyze_today_freezing()          # must NOT trigger a second 92-request sweep
    # exactly one full sweep when the fetch already failed
    assert len(calls) == len(iwm.INDIANA_CITIES)


def test_menu_refresh_does_not_destroy_good_data(tmp_path, monkeypatch):
    m = make_monitor(tmp_path)
    m.weather_data = {"Peru": make_payload()}
    m.data_fetched = True
    monkeypatch.setattr(m, "get_weather_data", lambda city, coords: None)
    answers = iter(["8", "10"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    m.run_interactive_mode()
    # option 8 with the network down must keep the good in-memory data
    # (the old handler wiped weather_data before fetching)
    assert "Peru" in m.weather_data
    assert m.data_fetched is True


def test_total_failure_serves_stale_cache(tmp_path, monkeypatch):
    m = make_monitor(tmp_path)
    write_cache(m.cache_file, {
        "timestamp": "2026-09-20 08:00:00",
        "weather_data": {"Peru": make_payload()},
    })
    old = os.path.getmtime(m.cache_file) - 7 * 3600
    os.utime(m.cache_file, (old, old))
    monkeypatch.setattr(m, "get_weather_data", lambda city, coords: None)
    m.fetch_all_weather_data()
    # live sweep failed, but the expired cache still holds good data:
    # serve it rather than leaving the monitor with nothing at all
    assert m.weather_data and "Peru" in m.weather_data
    assert m.data_fetched is True
    assert m.data_from_cache is True
    assert m.data_timestamp == "2026-09-20 08:00:00"


def test_partial_fetch_caches_successes_only(tmp_path, monkeypatch):
    m = make_monitor(tmp_path)
    cities = list(iwm.INDIANA_CITIES)
    good = make_payload()
    def fake_get(city, coords):
        return good if city == cities[0] else None
    monkeypatch.setattr(m, "get_weather_data", fake_get)
    m.fetch_all_weather_data()
    assert m.data_fetched is True
    assert list(m.weather_data.keys()) == [cities[0]]


def test_force_refresh_offline_keeps_previous_good_data(tmp_path, monkeypatch):
    m = make_monitor(tmp_path)
    m.weather_data = {"Peru": make_payload()}
    m.data_fetched = True
    m.data_timestamp = "2026-09-20 08:00:00"
    monkeypatch.setattr(m, "get_weather_data", lambda city, coords: None)
    m.fetch_all_weather_data(force_refresh=True)
    # last known-good data survives an offline force refresh
    assert m.weather_data == {"Peru": m.weather_data["Peru"]}
    assert m.data_fetched is True
    assert m.data_timestamp == "2026-09-20 08:00:00"
    import os
    # and the old cache file is not overwritten with an empty dict
    assert not os.path.exists(m.cache_file)


def test_force_refresh_partial_keeps_previous_good_data(tmp_path, monkeypatch):
    m = make_monitor(tmp_path)
    m.weather_data = {"Peru": make_payload(), "Muncie": make_payload()}
    m.data_fetched = True
    cities = list(iwm.INDIANA_CITIES)
    fresh = make_payload(min_temp=15.0)
    monkeypatch.setattr(m, "get_weather_data",
                        lambda city, coords: fresh if city == cities[0] else None)
    m.fetch_all_weather_data(force_refresh=True)
    # 1/92 succeeded: fresh wins for that city, previous good data survives
    # for the 91 that failed (the old code discarded them wholesale).
    assert m.weather_data[cities[0]] is fresh
    assert m.weather_data["Muncie"] is m.weather_data["Muncie"]
    assert len(m.weather_data) == 3      # Peru + Muncie (previous) + fresh Evansville
    assert m.data_fetched is True


def test_partial_fetch_falls_back_to_expired_cache_for_missed_cities(tmp_path, monkeypatch):
    m = make_monitor(tmp_path)
    write_cache(m.cache_file, {
        "timestamp": "2026-09-20 08:00:00",
        "weather_data": {"Peru": make_payload(), "Muncie": make_payload()},
    })
    # make the cache expired so the fetch actually sweeps
    old = os.path.getmtime(m.cache_file) - 7 * 3600
    os.utime(m.cache_file, (old, old))
    cities = list(iwm.INDIANA_CITIES)
    fresh = make_payload(min_temp=15.0)
    monkeypatch.setattr(m, "get_weather_data",
                        lambda city, coords: fresh if city == cities[0] else None)
    m.fetch_all_weather_data()
    # 1/92 succeeded: the freshly fetched city is served, and the other
    # 91 fall back to the expired cache's copies instead of vanishing
    # (the old code overwrote the 92-city cache with the 1-city partial).
    assert m.weather_data[cities[0]] is fresh
    assert m.weather_data["Muncie"] is not None   # kept from the old cache
    # and the rewritten cache still holds every city it had before
    with open(m.cache_file) as f:
        saved = json.load(f)["weather_data"]
    assert set(saved) == {cities[0], "Muncie", "Peru"}


def test_error_body_rejected_at_store_time(tmp_path, monkeypatch):
    m = make_monitor(tmp_path)
    monkeypatch.setattr(
        m, "get_weather_data",
        lambda city, coords: {"error": True, "reason": "quota exceeded"},
    )
    m.fetch_all_weather_data()
    assert m.weather_data == {}
    assert m.data_fetched is False


def test_get_weather_data_requests_mph(tmp_path, monkeypatch):
    m = make_monitor(tmp_path)
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return make_payload()

    def fake_get(url, params=None, timeout=None):
        captured["params"] = params
        return FakeResponse()

    monkeypatch.setattr(iwm.requests, "get", fake_get)
    data = m.get_weather_data("Peru", {"lat": 40.75, "lon": -86.07})
    assert data is not None
    assert captured["params"]["windspeed_unit"] == "mph"
    assert captured["params"]["temperature_unit"] == "fahrenheit"


@pytest.mark.parametrize("temp,expected", [
    (15, "SEVERE FREEZE"), (20, "SEVERE FREEZE"),
    (32, "FREEZE"), (33, "FROST WARNING"), (40, "FROST WARNING"),
    (41, "COOL"), (60, "COOL"),
    (61, "WARM"), (70, "WARM"),
    (71, "HOT"), (85, "HOT"),
    (86, "VERY HOT"), (92, "VERY HOT"),
])
def test_get_temp_status_boundaries(temp, expected):
    assert iwm.get_temp_status(temp) == expected


def test_no_legend_only_words():
    # The map legends must no longer promise WATCH/GOOD/COMFORTABLE
    import inspect
    src = inspect.getsource(iwm)
    assert "WATCH" not in src
    assert '"GOOD"' not in src and "GOOD" not in src.replace("Good choice", "")
    assert "COMFORTABLE" not in src


def test_state_summary_status_matches_shared_function(capsys, tmp_path):
    m = make_monitor(tmp_path)
    payload = make_payload(min_temp=92.0)
    # The state summary statuses the CURRENT temp, which make_payload
    # hardcodes to 55.0; pin it to 92 so the hot branch is exercised.
    payload["current_weather"]["temperature"] = 92.0
    m.weather_data = {"Peru": payload}
    m.data_fetched = True
    m.data_timestamp = "2026-09-21 09:00:00"
    m.display_state_summary()
    out = capsys.readouterr().out
    assert "VERY HOT" in out          # not "WARM"
    assert "WARM\n" not in out


def test_per_city_forecast_hot_label(capsys, tmp_path):
    m = make_monitor(tmp_path)
    m.weather_data = {"Peru": make_payload(min_temp=92.0)}
    m.data_fetched = True
    m.display_city_weather("Peru", {"lat": 40.75, "lon": -86.07}, "North")
    out = capsys.readouterr().out
    assert "VERY HOT" in out
    assert "WARM" not in out


def test_get_today_index():
    daily = {"time": ["2026-09-20", "2026-09-21", "2026-09-22"]}
    assert iwm.get_today_index(daily, "2026-09-21") == 1
    assert iwm.get_today_index(daily, "2026-09-25") == -1
    assert iwm.get_today_index({}, "2026-09-21") == -1


def test_today_lookups_use_indiana_timezone_not_local_clock(monkeypatch, tmp_path):
    # daily['time'] holds America/Indiana/Indianapolis-local dates, so the
    # "today" used for lookups must come from that timezone — a host west or
    # east of Indiana would otherwise match yesterday/tomorrow or no day.
    m = make_monitor(tmp_path)
    # The array holds the naive machine-local date: the faulty implementation
    # (datetime.now()) matches it and reports the city, while an Indiana-
    # timezone-aware lookup (patched below to a date no array contains) does not.
    today = datetime.now().strftime("%Y-%m-%d")
    m.weather_data = {"Peru": {
        "current_weather": {"temperature": 55.0},
        "daily": {"temperature_2m_min": [25.0], "temperature_2m_max": [40.0], "time": [today]},
    }}
    m.data_fetched = True
    # Claim "today" is a date no array contains while the local clock's date
    # IS in the array: with the Indiana-timezone seam the city is excluded;
    # with naive datetime.now() it leaks in as an analyzed city.
    monkeypatch.setattr(iwm, "indiana_today", lambda: "2099-01-01", raising=False)
    freezing, frost, above = m.analyze_today_freezing()
    assert freezing == [] and frost == [] and above == []


def test_get_daily_value_guards():
    data = {"daily": {"temperature_2m_min": [None, 45.2]}}
    assert iwm.get_daily_value(data, "temperature_2m_min", 1) == 45.2
    assert iwm.get_daily_value(data, "temperature_2m_min", 0) is None   # null skipped
    assert iwm.get_daily_value(data, "temperature_2m_min", 9) is None   # out of range
    assert iwm.get_daily_value({"error": True}, "temperature_2m_min", 0) is None


def test_is_valid_payload_gate_rejects_bools_and_missing_current_weather():
    payload = make_payload()
    assert iwm.is_valid_payload(payload) is True

    no_current = {"daily": payload["daily"]}
    assert iwm.is_valid_payload(no_current) is False           # older-build cache
    assert iwm.is_valid_payload(
        {"current_weather": {"windspeed": 5.0}, "daily": payload["daily"]}) is False
    assert iwm.is_valid_payload(
        {"current_weather": {"temperature": "55"}, "daily": payload["daily"]}) is False

    bools = make_payload()
    bools["daily"]["temperature_2m_min"][0] = True
    assert iwm.is_valid_payload(bools) is False                # bool is not a temperature
    assert iwm.get_daily_value(
        {"daily": {"temperature_2m_min": [True]}}, "temperature_2m_min", 0) is None


def test_today_analysis_uses_current_date_not_cache_day0(tmp_path):
    m = make_monitor(tmp_path)
    # Cache was fetched "yesterday": daily[0] is yesterday's date, but
    # analysis must key today by the real current date, not blind day 0.
    # Derive dates from the same source the code looks today up with,
    # so the test is valid regardless of the host's timezone.
    today = iwm.indiana_today()
    yesterday = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    m.weather_data = {"Peru": {
        "current_weather": {"temperature": 55.0},
        "daily": {
            "temperature_2m_min": [28.0, 50.0],
            "temperature_2m_max": [45.0, 70.0],
            "time": [yesterday, today],
        }
    }}
    m.data_fetched = True
    freezing, frost, above = m.analyze_today_freezing()
    # 28F was YESTERDAY's min; today's min is 50F -> must NOT be in freezing list
    assert freezing == [] and frost == []
    assert [c["city"] for c in above] == ["Peru"]


@pytest.fixture
def freeze_today(monkeypatch):
    class FakeDT(datetime):
        @classmethod
        def now(cls, *args, **kwargs):   # accepts tz arg like the real now()
            return datetime(2099, 1, 1)
    monkeypatch.setattr(iwm, "datetime", FakeDT)


def test_today_analysis_three_way_split(tmp_path, freeze_today):
    m = make_monitor(tmp_path)
    # Real INDIANA_CITIES names: analyze iterates INDIANA_CITIES, so fake
    # keys like "A"/"B"/"C" would never be visited.
    m.weather_data = {
        "Peru": {"current_weather": {"temperature": 55.0}, "daily": {"temperature_2m_min": [20.0], "temperature_2m_max": [40.0], "time": ["2099-01-01"]}},
        "Muncie": {"current_weather": {"temperature": 55.0}, "daily": {"temperature_2m_min": [35.0], "temperature_2m_max": [40.0], "time": ["2099-01-01"]}},
        "Evansville": {"current_weather": {"temperature": 55.0}, "daily": {"temperature_2m_min": [50.0], "temperature_2m_max": [70.0], "time": ["2099-01-01"]}},
    }
    m.data_fetched = True
    freezing, frost, above = m.analyze_today_freezing()
    assert [c["city"] for c in freezing] == ["Peru"]
    assert [c["city"] for c in frost] == ["Muncie"]     # 35F = FROST WARNING bucket, not "MILD"
    assert [c["city"] for c in above] == ["Evansville"]


def test_empty_today_analysis_reports_no_data_not_safety_claims(tmp_path, capsys):
    m = make_monitor(tmp_path)
    m.weather_data = {}          # offline first run: nothing was analyzed
    m.data_fetched = True
    m.display_today_freezing_analysis()
    out = capsys.readouterr().out
    assert "No city data" in out
    assert "No cities with freezing temperatures today!" not in out
    assert "All cities have freezing temperatures today!" not in out


def test_empty_week_analysis_reports_no_data_not_safety_claims(tmp_path, capsys):
    m = make_monitor(tmp_path)
    m.weather_data = {}
    m.data_fetched = True
    m.display_week_freezing_analysis()
    out = capsys.readouterr().out
    assert "No city data" in out
    assert "No cities with freezing temperatures this week!" not in out
    assert "All cities have freezing temperatures this week!" not in out


def test_state_summary_header_shows_data_timestamp(capsys, tmp_path):
    m = make_monitor(tmp_path)
    m.weather_data = {"Peru": make_payload()}
    m.data_fetched = True
    m.data_timestamp = "2026-09-21 03:00:00"
    m.data_from_cache = True
    m.display_state_summary()
    out = capsys.readouterr().out
    assert "2026-09-21 03:00:00" in out
    assert "(cached)" in out


def test_state_summary_skips_city_without_current_weather(capsys, tmp_path):
    m = make_monitor(tmp_path)
    # Stale older-build payload: well-formed daily arrays, no current_weather
    m.weather_data = {
        "Muncie": {"daily": {"temperature_2m_min": [30.0], "temperature_2m_max": [45.0], "time": ["2026-09-21"]}},
        "Peru": make_payload(),
    }
    m.data_fetched = True
    m.display_state_summary()   # used to raise KeyError: 'current_weather'
    out = capsys.readouterr().out
    assert "Peru" in out        # the other city still renders
    assert not any(l.startswith("Muncie") for l in out.splitlines())


def test_today_analysis_survives_unknown_cache_keys(tmp_path, capsys):
    m = make_monitor(tmp_path)
    # Daily dates must track the runtime date or get_today_index returns -1
    # on every other calendar day (same fault as the day-0 test above).
    today = datetime.now().strftime("%Y-%m-%d")
    # Cache written by the old 13-city build: contains "Gary", missing from INDIANA_CITIES
    m.weather_data = {
        "Gary": {"current_weather": {"temperature": 55.0}, "daily": {"temperature_2m_min": [10.0], "temperature_2m_max": [20.0], "time": [today]}},
        "Peru": {"current_weather": {"temperature": 55.0}, "daily": {"temperature_2m_min": [25.0], "temperature_2m_max": [40.0], "time": [today]}},
    }
    m.data_fetched = True
    freezing, frost, above = m.analyze_today_freezing()   # used to raise KeyError: 'Gary'
    assert [c["city"] for c in freezing] == ["Peru"]


def test_week_analysis_survives_unknown_cache_keys(tmp_path):
    m = make_monitor(tmp_path)
    m.weather_data = {
        "Gary": {"current_weather": {"temperature": 55.0}, "daily": {"temperature_2m_min": [10.0] * 7, "temperature_2m_max": [20.0] * 7, "time": ["2026-09-2%d" % d for d in range(1, 8)]}},
        "Peru": {"current_weather": {"temperature": 55.0}, "daily": {"temperature_2m_min": [25.0] * 7, "temperature_2m_max": [40.0] * 7, "time": ["2026-09-2%d" % d for d in range(1, 8)]}},
    }
    m.data_fetched = True
    freezing, no_freezing = m.analyze_week_freezing()     # used to raise KeyError at 1058
    assert [c["city"] for c in freezing] == ["Peru"]


def test_null_daily_value_skips_one_city_not_whole_view(tmp_path):
    m = make_monitor(tmp_path)
    m.weather_data = {
        "Broken": {"current_weather": {"temperature": 55.0}, "daily": {"temperature_2m_min": [None, 45.0], "temperature_2m_max": [60.0, 60.0], "time": ["2026-09-21", "2026-09-22"]}},
        "Peru": {"current_weather": {"temperature": 55.0}, "daily": {"temperature_2m_min": [25.0, 30.0], "temperature_2m_max": [40.0, 40.0], "time": ["2026-09-21", "2026-09-22"]}},
    }
    m.data_fetched = True
    # coldest-temp mapping must skip Broken (min over nulls used to raise TypeError)
    result = m.get_county_temperature_data()
    assert "Broken" not in [v["city"] for v in result.values()]
    assert any(v["city"] == "Peru" for v in result.values())


def test_city_view_retries_live_when_prefetch_missed(tmp_path, monkeypatch, capsys):
    m = make_monitor(tmp_path)
    m.weather_data = {}          # Jasper failed during the bulk fetch
    m.data_fetched = True
    monkeypatch.setattr(m, "get_weather_data", lambda city, coords: make_payload(min_temp=28.0))
    m.display_city_weather("Jasper", {"lat": 38.39, "lon": -86.93}, "Southwest")
    out = capsys.readouterr().out
    assert "No data available" not in out
    assert "FREEZE" in out or "FROST WARNING" in out
    assert m.weather_data.get("Jasper") is not None   # live result cached in memory


def test_city_view_reports_failure_when_retry_also_fails(tmp_path, monkeypatch, capsys):
    m = make_monitor(tmp_path)
    m.weather_data = {}
    m.data_fetched = True
    monkeypatch.setattr(m, "get_weather_data", lambda city, coords: None)
    m.display_city_weather("Jasper", {"lat": 38.39, "lon": -86.93}, "Southwest")
    assert "No data available" in capsys.readouterr().out


ALLOWED_REGIONS = {
    "North", "Northeast", "Northwest", "Central", "East Central",
    "West Central", "South Central", "Southeast", "Southwest",
}


def test_every_city_has_a_region():
    bad = sorted(
        c for c, coords in iwm.INDIANA_CITIES.items()
        if coords.get("region", "") not in ALLOWED_REGIONS
    )
    assert not bad, f"{len(bad)} cities with blank/unknown region: {bad}"


def test_freezing_tables_have_regions(tmp_path, capsys, freeze_today):
    m = make_monitor(tmp_path)
    payload = make_payload(min_temp=25.0)
    # make_payload pins its daily dates to 2026-09-21; re-pin to the date the
    # freeze_today fixture serves, mirroring test_today_analysis_three_way_split.
    payload["daily"]["time"] = ["2099-01-01", "2099-01-02"]
    for city in ("Marion", "Peru"):     # Marion's region was blank at HEAD
        m.weather_data[city] = payload
    m.data_fetched = True
    m.display_today_freezing_analysis()
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.startswith("Marion")]
    assert lines, "Marion missing from today's freezing table entirely"
    # Table rows render as f"{city:<15} {region:<12} {min_temp:>7.1f}..." so the
    # Region cell occupies columns 16-27; a blank region renders as whitespace.
    region_cell = lines[0][16:28].strip()
    assert region_cell in ALLOWED_REGIONS, f"Marion Region cell is {region_cell!r}"
