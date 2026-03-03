"""Tests for topx.py — stub interface validation + HTTP endpoint tests."""

import pytest
from collections import Counter

import topx
from topx import (
    app,
    get_pod_index,
    get_byte_partition,
    count_partition,
    merge_counters,
    top_x,
)


# ---------------------------------------------------------------------------
# Flask test client fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# HTTP endpoint tests (stub responses must be correctly shaped)
# ---------------------------------------------------------------------------

def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_status_returns_200(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert "status" in resp.get_json()


def test_results_returns_200(client):
    resp = client.get("/results")
    assert resp.status_code == 200
    data = resp.get_json()
    # Either mapper format (has "counts") or reducer format (has "results")
    assert "counts" in data or "results" in data


def test_results_mapper_mode(client):
    topx.MODE = "mapper"
    resp = client.get("/results")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "counts" in data
    assert isinstance(data["counts"], dict)


def test_results_reducer_mode(client):
    topx.MODE = "reducer"
    resp = client.get("/results")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert "top_x" in data


# ---------------------------------------------------------------------------
# Core function interface tests (stubs return correct types)
# ---------------------------------------------------------------------------

def test_get_pod_index_returns_int():
    result = get_pod_index()
    assert isinstance(result, int)


def test_get_byte_partition_returns_tuple():
    result = get_byte_partition("/tmp/test.csv", 0, 3)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_count_partition_returns_counter():
    result = count_partition("/tmp/test.csv", 0, 100)
    assert isinstance(result, Counter)


def test_merge_counters_returns_counter():
    result = merge_counters([Counter({"a": 1}), Counter({"b": 2})])
    assert isinstance(result, Counter)


def test_top_x_returns_list():
    result = top_x(Counter({"a": 5, "b": 3}), 10)
    assert isinstance(result, list)
