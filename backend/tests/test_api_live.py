"""Live API test script for VARUNEETI forecast endpoint."""
import httpx
import json
import sys

BASE = "http://127.0.0.1:8000"

def test_health():
    print("=== TEST 1: Health Endpoint ===")
    r = httpx.get(f"{BASE}/api/health")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    assert r.status_code == 200
    return True

def test_lanes():
    print("\n=== TEST 2: Lanes Endpoint ===")
    r = httpx.get(f"{BASE}/api/lanes")
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Available lanes: {data['count']}")
    assert r.status_code == 200
    assert data["count"] > 0
    return True

def test_default_demo():
    print("\n=== TEST 3: Default Demo (Australia->Paradip, Panamax, 30d) ===")
    r = httpx.post(f"{BASE}/api/forecast", json={
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_type": "Panamax",
        "horizon_days": 30,
    }, timeout=30)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Forecast:     {data['forecast']} USD/tonne")
    print(f"Lower bound:  {data['lower_bound']}")
    print(f"Upper bound:  {data['upper_bound']}")
    print(f"Trend:        {data['trend']}")
    print(f"Volatility:   {data['volatility']}")
    print(f"Confidence:   {data['confidence']}")
    print(f"Model:        {data['model_name']}")
    print(f"Model wins:   {data['model_wins']}")
    print(f"Baseline MAE: {data['baseline_error']['mae']}")
    print(f"Model MAE:    {data['model_error']['mae']}")
    print(f"Historical:   {len(data['historical_series'])} points")
    print(f"Forecast pts: {len(data['forecast_series'])} points")
    print(f"Data source:  {data['data_source']}")
    print(f"Warnings:     {data['warnings']}")
    bounds_ok = data["lower_bound"] <= data["forecast"] <= data["upper_bound"]
    print(f"Bounds OK:    {bounds_ok}")
    assert r.status_code == 200
    assert bounds_ok
    return True

def test_unknown_lane():
    print("\n=== TEST 4: Unknown Lane ===")
    r = httpx.post(f"{BASE}/api/forecast", json={
        "origin": "Mars",
        "destination": "Jupiter",
        "vessel_type": "Spaceship",
        "horizon_days": 30,
    })
    print(f"Status: {r.status_code} (expected 400)")
    assert r.status_code == 400
    return True

def test_different_horizons():
    print("\n=== TEST 5: Different Horizons ===")
    for h in [7, 14, 30, 60, 90]:
        r = httpx.post(f"{BASE}/api/forecast", json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_type": "Panamax",
            "horizon_days": h,
        }, timeout=30)
        data = r.json()
        print(f"  {h:3d}d -> forecast={data['forecast']:.2f}, conf={data['confidence']:.3f}, model={data['model_name']}")
        assert r.status_code == 200
    return True

def test_different_vessels():
    print("\n=== TEST 6: Different Vessel Types (Australia->Paradip) ===")
    for vt in ["Handysize", "Supramax", "Panamax", "Capesize"]:
        r = httpx.post(f"{BASE}/api/forecast", json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_type": vt,
            "horizon_days": 30,
        }, timeout=30)
        data = r.json()
        print(f"  {vt:12s} -> forecast={data['forecast']:.2f}, trend={data['trend']}, vol={data['volatility']}")
        assert r.status_code == 200
    return True

def test_different_lanes():
    print("\n=== TEST 7: Different Lanes ===")
    lanes = [
        ("Indonesia", "Dhamra", "Supramax"),
        ("USA", "Haldia", "Panamax"),
        ("Mozambique", "Gangavaram", "Handysize"),
        ("Russia", "Paradip", "Capesize"),
    ]
    for origin, dest, vt in lanes:
        r = httpx.post(f"{BASE}/api/forecast", json={
            "origin": origin,
            "destination": dest,
            "vessel_type": vt,
            "horizon_days": 30,
        }, timeout=30)
        data = r.json()
        print(f"  {origin:12s}->{dest:15s} [{vt:10s}] -> {data['forecast']:.2f} USD/t, model={data['model_name']}")
        assert r.status_code == 200
    return True

def test_full_json_response():
    print("\n=== TEST 8: Full JSON Response Structure ===")
    r = httpx.post(f"{BASE}/api/forecast", json={
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_type": "Panamax",
        "horizon_days": 30,
    }, timeout=30)
    data = r.json()
    print(json.dumps(data, indent=2))
    return True


if __name__ == "__main__":
    tests = [
        test_health,
        test_lanes,
        test_default_demo,
        test_unknown_lane,
        test_different_horizons,
        test_different_vessels,
        test_different_lanes,
        test_full_json_response,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"\n  FAILED: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    if failed:
        sys.exit(1)
    print("ALL LIVE API TESTS PASSED")
