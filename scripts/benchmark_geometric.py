"""Mede tempo em seis tamanhos geometricos com seis linhas livres.

Complementa o experimento de tabuleiros vazios: a variacao de n aqui e
geometrica, enquanto m=6 mantem a busca fatorial executavel nas quatro versoes.
"""

from __future__ import annotations

import csv
import json
import platform
import shutil
import statistics
import sys
from pathlib import Path

from benchmark import compile_cpp, run

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results"
REPETITIONS = 15
WARMUP = 3


def main() -> None:
    manifest = json.loads((ROOT / "data" / "memory_inputs" / "manifest.json").read_text(encoding="utf-8"))
    binary = compile_cpp()
    raw = []
    summary = []
    for instance in manifest["instances"]:
        name = str(instance["name"])
        n = int(instance["n"])
        path = str(ROOT / str(instance["file"]))
        expected = None
        for language in ("Python", "C++"):
            for algorithm in ("brute", "backtracking"):
                if language == "Python":
                    command = [sys.executable, str(ROOT / "src" / "python" / "nqueens.py"),
                               algorithm, path, "--repetitions", str(REPETITIONS), "--warmup", str(WARMUP)]
                else:
                    command = [str(binary), algorithm, path, str(REPETITIONS), str(WARMUP)]
                samples = list(csv.reader(run(command).splitlines()))
                if len(samples) != REPETITIONS:
                    raise AssertionError(f"repeticoes faltando: {name} {language} {algorithm}")
                times = []
                operations = None
                for repetition, sample in enumerate(samples, 1):
                    count, current_operations, time_ns = map(int, sample)
                    if expected is None:
                        expected = count
                    if count != expected:
                        raise AssertionError(f"contagens divergentes: {name}")
                    if operations is None:
                        operations = current_operations
                    if current_operations != operations:
                        raise AssertionError(f"operacoes divergentes: {name}")
                    times.append(time_ns / 1e6)
                    raw.append({"instance": name, "n": n, "free_rows": 6,
                                "language": language, "algorithm": algorithm,
                                "repetition": repetition, "solutions": count,
                                "operations": current_operations, "time_ns": time_ns})
                summary.append({"instance": name, "n": n, "free_rows": 6,
                                "language": language, "algorithm": algorithm,
                                "solutions": expected, "operations": operations,
                                "repetitions": REPETITIONS, "mean_ms": statistics.mean(times),
                                "sd_ms": statistics.stdev(times),
                                "median_ms": statistics.median(times)})
        print(f"{name}: {expected} solucoes", flush=True)
    RESULTS.mkdir(exist_ok=True)
    for filename, rows in (("geometric_raw.csv", raw), ("geometric_summary.csv", summary)):
        with (RESULTS / filename).open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    environment = {
        "platform": platform.platform(), "python": sys.version,
        "compiler": run([shutil.which("g++"), "--version"]).splitlines()[0],
        "flags": "-O2 -std=c++17 -Wall -Wextra", "repetitions": REPETITIONS,
        "warmup": WARMUP, "sizes": [item["n"] for item in manifest["instances"]],
        "free_rows": 6, "input_manifest": "data/memory_inputs/manifest.json",
    }
    (RESULTS / "geometric_environment.json").write_text(
        json.dumps(environment, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Salvas {len(raw)} medicoes de tempo em escala geometrica")


if __name__ == "__main__":
    main()
