"""Tests for generate_data.py — stub interface validation."""

from generate_data import build_url_pool, generate_zipf_indices, write_csv


def test_build_url_pool_returns_list():
    result = build_url_pool()
    assert isinstance(result, list)


def test_generate_zipf_indices_returns_list():
    result = generate_zipf_indices(100, 10, seed=42)
    assert isinstance(result, list)


def test_write_csv_returns_int():
    result = write_csv("/tmp/test_stub.csv", [], [])
    assert isinstance(result, int)
