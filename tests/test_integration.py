"""Integration tests against the live k8s cluster.

Requires reducer service reachable at http://127.0.0.1:30080 (NodePort).
Run with: pytest tests/test_integration.py -v

These tests are EXPECTED TO FAIL until MapReduce logic is implemented.
"""

import pytest
import requests

BASE_URL = "http://127.0.0.1:30080"


@pytest.fixture(scope="module")
def reducer_url():
    """Verify reducer is reachable; skip all tests if not."""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        resp.raise_for_status()
    except Exception as e:
        pytest.skip(f"Reducer not reachable at {BASE_URL}: {e}")
    return BASE_URL


def test_health_live(reducer_url):
    """Health endpoint should always return ok."""
    resp = requests.get(f"{reducer_url}/health", timeout=5)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_results_response_shape(reducer_url):
    """Results response must have required top-level keys."""
    resp = requests.get(f"{reducer_url}/results", timeout=30)
    assert resp.status_code == 200
    data = resp.json()
    assert "top_x" in data
    assert "results" in data
    assert "total_unique_urls" in data
    assert "total_url_hits" in data


def test_results_have_entries(reducer_url):
    """Top-X results should contain URL entries. FAILS until logic is implemented."""
    resp = requests.get(f"{reducer_url}/results", timeout=30)
    data = resp.json()
    assert len(data["results"]) > 0, (
        f"Expected top-X results but got empty list — "
        f"MapReduce logic not implemented yet"
    )


def test_total_hits_nonzero(reducer_url):
    """Total URL hits across all mappers should be > 0. FAILS until logic is implemented."""
    resp = requests.get(f"{reducer_url}/results", timeout=30)
    data = resp.json()
    assert data["total_url_hits"] > 0, (
        f"Expected total_url_hits > 0 but got {data['total_url_hits']} — "
        f"MapReduce logic not implemented yet"
    )


def test_top_result_fields(reducer_url):
    """Each result entry must have url (str) and count (int > 0). FAILS until logic is implemented."""
    resp = requests.get(f"{reducer_url}/results", timeout=30)
    data = resp.json()
    results = data["results"]
    assert len(results) > 0, "No results to validate — MapReduce logic not implemented yet"
    for entry in results:
        assert "url" in entry, f"Missing 'url' in {entry}"
        assert "count" in entry, f"Missing 'count' in {entry}"
        assert isinstance(entry["count"], int)
        assert entry["count"] > 0
