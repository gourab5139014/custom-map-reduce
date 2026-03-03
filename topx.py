#!/usr/bin/env python3
"""
topx.py - MapReduce Top-X URL frequency counter.

Usage:
    python topx.py --mode mapper
    python topx.py --mode reducer
"""

import argparse
import os
import socket
from collections import Counter

from flask import Flask, jsonify

app = Flask(__name__)

# Set by main() before Flask starts; routes branch on this value.
MODE: str = "reducer"


# ---------------------------------------------------------------------------
# Core functions (stubs — to be implemented)
# ---------------------------------------------------------------------------

def get_pod_index() -> int:
    """Parse ordinal from hostname (e.g. mapper-2 → 2). TODO: implement."""
    return 0


def get_byte_partition(filepath: str, pod_index: int, num_pods: int) -> tuple[int, int]:
    """Return (start_byte, end_byte) for this pod's partition. TODO: implement."""
    return (0, 0)


def count_partition(filepath: str, start_byte: int, end_byte: int) -> Counter:
    """Count URL occurrences in the given byte range. TODO: implement."""
    return Counter()


def merge_counters(counters: list[Counter]) -> Counter:
    """Sum-merge a list of Counters. TODO: implement."""
    return Counter()


def top_x(counter: Counter, x: int) -> list[tuple[str, int]]:
    """Return top-x (url, count) pairs sorted descending. TODO: implement."""
    return []


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/status")
def status():
    if MODE == "mapper":
        return jsonify({
            "status": "ready",
            "pod": socket.gethostname(),
            "rows_processed": 0,
        }), 200
    return jsonify({"status": "ready"}), 200


@app.route("/results")
def results():
    if MODE == "mapper":
        return jsonify({
            "pod": socket.gethostname(),
            "counts": {},
        }), 200
    # reducer
    top_x_val = int(os.environ.get("TOP_X", "10"))
    return jsonify({
        "top_x": top_x_val,
        "total_unique_urls": 0,
        "total_url_hits": 0,
        "query_time_seconds": 0.0,
        "results": [],
    }), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    global MODE
    parser = argparse.ArgumentParser(description="MapReduce Top-X URL processor")
    parser.add_argument("--mode", choices=["mapper", "reducer"], required=True)
    args = parser.parse_args()
    MODE = args.mode

    port = int(os.environ.get("PORT", "8080"))
    print(f"Starting in {MODE} mode on :{port}")
    app.run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    main()
