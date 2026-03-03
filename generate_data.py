#!/usr/bin/env python3
"""
generate_data.py - URL dataset generator for MapReduce.

Usage:
    python generate_data.py [--rows N] [--output PATH] [--seed S]
"""

import argparse
import os


def build_url_pool() -> list[str]:
    """Return pool of ~200 unique URLs. TODO: implement."""
    return []


def generate_zipf_indices(n_rows: int, n_urls: int, seed: int) -> list[int]:
    """Return Zipf-distributed indices into the URL pool. TODO: implement."""
    return []


def write_csv(output_path: str, url_pool: list[str], indices: list[int]) -> int:
    """Write URL rows to CSV, return bytes written. TODO: implement."""
    return 0


def write_metadata(metadata_path: str, total_rows: int, output_path: str, elapsed: float) -> None:
    """Write JSON metadata sentinel file. TODO: implement."""
    pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate URL frequency dataset")
    parser.add_argument("--rows", type=int, default=10_000_000, help="Number of rows")
    parser.add_argument("--output", type=str, default="/data/input.csv", help="Output CSV path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    metadata_path = os.path.join(os.path.dirname(args.output) or ".", "metadata.json")

    url_pool = build_url_pool()
    indices = generate_zipf_indices(args.rows, len(url_pool), args.seed)
    write_csv(args.output, url_pool, indices)
    write_metadata(metadata_path, args.rows, args.output, 0.0)


if __name__ == "__main__":
    main()
