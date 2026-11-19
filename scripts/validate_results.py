"""Audita entradas, CSVs e estatisticas antes de gerar os documentos."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results"
COMBINATIONS = {(language, algorithm) for language in ("Python", "C++")
                for algorithm in ("brute", "backtracking")}


def rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def close(actual: str, expected: float, label: str) -> None:
    if not math.isclose(float(actual), expected, rel_tol=1e-10, abs_tol=1e-9):
        raise AssertionError(f"{label}: {actual} != {expected}")


def validate_series(prefix: str, manifest_path: str, metric: str, mean: str, sd: str,
                    median: str | None, environment_name: str) -> tuple[int, int]:
    manifest = json.loads((ROOT / manifest_path).read_text(encoding="utf-8"))
    environment = json.loads((RESULTS / environment_name).read_text(encoding="utf-8"))
    repetitions = int(environment["repetitions"])
    assert repetitions >= 15, f"{prefix}: menos de 15 repeticoes"
    if prefix != "memory_":
        assert int(environment["warmup"]) == 3, f"{prefix}: aquecimento diferente"
    raw = rows(prefix + "raw.csv")
    summary = rows(prefix + "summary.csv")
    instances = {item["name"]: item for item in manifest["instances"]}
    assert len(instances) == len(manifest["instances"]), "nomes repetidos no manifesto"
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for item in raw:
        key = item["instance"], item["language"], item["algorithm"]
        assert key[0] in instances and key[1:] in COMBINATIONS, key
        grouped[key].append(item)
    expected_keys = {(name, language, algorithm) for name in instances
                     for language, algorithm in COMBINATIONS}
    assert set(grouped) == expected_keys, f"{prefix}: combinacoes ausentes ou extras"
    summary_by_key = {(item["instance"], item["language"], item["algorithm"]): item
                      for item in summary}
    assert len(summary_by_key) == len(summary) and set(summary_by_key) == expected_keys
    for name, instance in instances.items():
        path = ROOT / instance["file"]
        numbers = [int(part) for part in path.read_text(encoding="utf-8").split()]
        n, k = numbers[:2]
        assert n == int(instance["n"]) and len(numbers) == 2 + 2 * k
        fixed = {numbers[i]: numbers[i + 1] for i in range(2, len(numbers), 2)}
        assert len(fixed) == k and all(0 <= r < n and 0 <= c < n for r, c in fixed.items())
        if "fixed" in instance:
            assert fixed == {int(r): int(c) for r, c in instance["fixed"].items()}
        if "free_rows" in instance:
            assert n - k == int(instance["free_rows"]) == 6
        counts = set()
        for language, algorithm in COMBINATIONS:
            key = name, language, algorithm
            samples = grouped[key]
            assert len(samples) == repetitions, key
            assert {int(item["repetition"]) for item in samples} == set(range(1, repetitions + 1))
            assert {int(item["n"]) for item in samples} == {n}
            counts.update(int(item["solutions"]) for item in samples)
            assert len({item["operations"] for item in samples}) == 1, key
            values = [int(item[metric]) / (1e6 if metric == "time_ns" else 1)
                      for item in samples]
            assert all(value >= 0 for value in values)
            aggregate = summary_by_key[key]
            assert int(aggregate["repetitions"]) == repetitions
            assert int(aggregate["solutions"]) == int(samples[0]["solutions"])
            close(aggregate[mean], statistics.mean(values), str(key) + " media")
            close(aggregate[sd], statistics.stdev(values), str(key) + " desvio")
            if median:
                close(aggregate[median], statistics.median(values), str(key) + " mediana")
            if "min_ms" in aggregate:
                close(aggregate["min_ms"], min(values), str(key) + " minimo")
                close(aggregate["max_ms"], max(values), str(key) + " maximo")
            if "min_peak_bytes" in aggregate:
                close(aggregate["min_peak_bytes"], min(values), str(key) + " minimo")
                close(aggregate["max_peak_bytes"], max(values), str(key) + " maximo")
        assert len(counts) == 1, f"{name}: contagens divergentes"
    return len(raw), len(summary)


def main() -> None:
    specifications = (
        ("", "data/inputs/manifest.json", "time_ns", "mean_ms", "sd_ms", "median_ms", "environment.json"),
        ("geometric_", "data/memory_inputs/manifest.json", "time_ns", "mean_ms", "sd_ms", "median_ms", "geometric_environment.json"),
        ("memory_", "data/memory_inputs/manifest.json", "peak_heap_bytes", "mean_peak_bytes", "sd_peak_bytes", None, "memory_environment.json"),
    )
    for spec in specifications:
        raw_count, summary_count = validate_series(*spec)
        print(f"{spec[0] or 'principal'}: {raw_count} amostras, {summary_count} agregados conferidos")


if __name__ == "__main__":
    main()
