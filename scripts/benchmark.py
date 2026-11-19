"""Executa as quatro combinacoes, testa corretude e salva medidas brutas."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "results" / "raw.csv"
SUMMARY = ROOT / "data" / "results" / "summary.csv"
KNOWN_EMPTY = {4: 2, 5: 10, 6: 4, 7: 40, 8: 92, 9: 352, 10: 724}


def run(command: list[str]) -> str:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    return completed.stdout


def hardware_details() -> dict[str, object]:
    """Registra CPU e RAM fisica sem dependencias externas."""
    details: dict[str, object] = {"cpu_name": platform.processor(), "ram_bytes": None}
    if os.name == "nt":
        import ctypes
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            details["cpu_name"] = str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()

        class MemoryStatus(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in (
                    "ullTotalPhys", "ullAvailPhys", "ullTotalPageFile", "ullAvailPageFile",
                    "ullTotalVirtual", "ullAvailVirtual", "ullAvailExtendedVirtual")]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            details["ram_bytes"] = int(status.ullTotalPhys)
    elif hasattr(os, "sysconf"):
        try:
            details["ram_bytes"] = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError):
            pass
    return details


def compile_cpp() -> Path:
    compiler = shutil.which("g++")
    if compiler is None:
        raise RuntimeError("g++ nao encontrado")
    binary = ROOT / "build" / ("nqueens.exe" if os.name == "nt" else "nqueens")
    binary.parent.mkdir(exist_ok=True)
    run([compiler, "-O2", "-std=c++17", "-Wall", "-Wextra", "-o", str(binary), str(ROOT / "src" / "cpp" / "nqueens.cpp")])
    return binary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=15)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--names", nargs="*", help="subconjunto opcional para testes rapidos")
    args = parser.parse_args()
    if args.repetitions < 15 and args.names is None:
        parser.error("a medicao final exige pelo menos 15 repeticoes")
    manifest = json.loads((ROOT / "data" / "inputs" / "manifest.json").read_text(encoding="utf-8"))
    instances = manifest["instances"]
    if args.names:
        names = set(args.names)
        instances = [item for item in instances if item["name"] in names]
        if len(instances) != len(names):
            parser.error("nome de instancia inexistente")
    binary = compile_cpp()
    rows: list[dict[str, object]] = []
    for instance in instances:
        expected_count = None
        for language in ("Python", "C++"):
            for algorithm in ("brute", "backtracking"):
                path = str(ROOT / instance["file"])
                command = ([sys.executable, str(ROOT / "src" / "python" / "nqueens.py")]
                           if language == "Python" else [str(binary)])
                output = run(command + [algorithm, path, str(args.repetitions), str(args.warmup)]
                             if language == "C++" else
                             command + [algorithm, path, "--repetitions", str(args.repetitions), "--warmup", str(args.warmup)])
                samples = list(csv.reader(output.splitlines()))
                if len(samples) != args.repetitions:
                    raise AssertionError(f"numero de amostras incorreto: {instance['name']} {language} {algorithm}")
                for index, sample in enumerate(samples, 1):
                    count, operations, ns = map(int, sample)
                    if expected_count is None:
                        expected_count = count
                    if count != expected_count:
                        raise AssertionError(f"divergencia de corretude: {instance['name']}")
                    rows.append({"instance": instance["name"], "n": instance["n"],
                                 "fixed_count": len(instance["fixed"]), "language": language,
                                 "algorithm": algorithm, "repetition": index,
                                 "solutions": count, "operations": operations, "time_ns": ns})
        if instance["name"].startswith("empty_") and instance["n"] in KNOWN_EMPTY:
            if expected_count != KNOWN_EMPTY[instance["n"]]:
                raise AssertionError(f"contagem conhecida incorreta para n={instance['n']}")
        print(f"{instance['name']}: {expected_count} solucoes", flush=True)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with RAW.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    groups: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for row in rows:
        groups.setdefault((str(row["instance"]), str(row["language"]), str(row["algorithm"])), []).append(row)
    summary = []
    for (name, language, algorithm), group in groups.items():
        times = [int(row["time_ns"]) / 1e6 for row in group]
        first = group[0]
        summary.append({"instance": name, "n": first["n"], "fixed_count": first["fixed_count"],
                        "language": language, "algorithm": algorithm, "solutions": first["solutions"],
                        "operations": first["operations"], "repetitions": len(group),
                        "mean_ms": statistics.mean(times),
                        "sd_ms": statistics.stdev(times) if len(times) > 1 else 0,
                        "median_ms": statistics.median(times), "min_ms": min(times), "max_ms": max(times),
                        "factorial_n": math.factorial(int(first["n"]))})
    with SUMMARY.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    env = {"platform": platform.platform(), "processor": platform.processor(),
           "python": sys.version, "compiler": run([shutil.which("g++"), "--version"]).splitlines()[0],
           "flags": "-O2 -std=c++17 -Wall -Wextra", "seed": manifest["seed"],
           "repetitions": args.repetitions, "warmup": args.warmup}
    env.update(hardware_details())
    (RAW.parent / "environment.json").write_text(json.dumps(env, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Salvos {len(rows)} tempos em {RAW}")


if __name__ == "__main__":
    main()
