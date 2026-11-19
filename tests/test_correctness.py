"""Testes de referencia e concordancia das quatro implementacoes."""

from __future__ import annotations

import importlib.util
import itertools
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nqueens", ROOT / "src" / "python" / "nqueens.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CorrectnessTests(unittest.TestCase):
    def test_independent_oracle_for_small_partial_boards(self) -> None:
        """Compara ambas as buscas com permutacoes da biblioteca padrao."""
        for n in range(1, 6):
            for placement in itertools.product(range(-1, n), repeat=min(n, 2)):
                fixed = list(placement) + [-1] * (n - len(placement))
                expected = sum(
                    all(fixed[r] < 0 or fixed[r] == cols[r] for r in range(n))
                    and len({r - c for r, c in enumerate(cols)}) == n
                    and len({r + c for r, c in enumerate(cols)}) == n
                    for cols in itertools.permutations(range(n))
                )
                with self.subTest(n=n, fixed=fixed):
                    self.assertEqual(module.brute_force(n, fixed)[0], expected)
                    self.assertEqual(module.backtracking(n, fixed)[0], expected)

    def test_invalid_instance_rejected_by_both_languages(self) -> None:
        binary = ROOT / "build" / ("nqueens.exe" if sys.platform == "win32" else "nqueens")
        self.assertTrue(binary.exists(), "compile primeiro com scripts/benchmark.py")
        for contents in ("0 0\n", "4 2\n0 1\n0 2\n", "4 1\n4 0\n", "4 0\nextra\n"):
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "invalid.txt"
                path.write_text(contents, encoding="utf-8")
                with self.subTest(contents=contents):
                    with self.assertRaises(ValueError):
                        module.read_instance(path)
                    for algorithm in ("brute", "backtracking"):
                        result = subprocess.run([str(binary), algorithm, str(path)], capture_output=True, text=True)
                        self.assertNotEqual(result.returncode, 0)

    def test_known_empty_boards(self) -> None:
        known = {1: 1, 2: 0, 3: 0, 4: 2, 5: 10, 6: 4, 7: 40, 8: 92, 9: 352}
        for n, expected in known.items():
            fixed = [-1] * n
            self.assertEqual(module.brute_force(n, fixed)[0], expected)
            self.assertEqual(module.backtracking(n, fixed)[0], expected)

    def test_fixed_queens(self) -> None:
        fixtures = [
            (4, [-1, -1, -1, -1], 2),
            (4, [0, -1, -1, -1], 0),
            (4, [1, -1, -1, -1], 1),
            (4, [1, 3, 0, 2], 1),
            (4, [0, 0, -1, -1], 0),
        ]
        for n, fixed, expected in fixtures:
            self.assertEqual(module.brute_force(n, fixed)[0], expected)
            self.assertEqual(module.backtracking(n, fixed)[0], expected)

    def test_cpp_matches_python_on_every_generated_input(self) -> None:
        binary = ROOT / "build" / ("nqueens.exe" if sys.platform == "win32" else "nqueens")
        self.assertTrue(binary.exists(), "compile primeiro com scripts/benchmark.py")
        for path in sorted((ROOT / "data" / "inputs").glob("*.txt")):
            n, fixed = module.read_instance(path)
            for algorithm, python_function in (("brute", module.brute_force), ("backtracking", module.backtracking)):
                with self.subTest(path=path.name, algorithm=algorithm):
                    output = subprocess.check_output([str(binary), algorithm, str(path)], text=True)
                    cpp_count, cpp_ops, _ = map(int, output.strip().split(","))
                    self.assertEqual((cpp_count, cpp_ops), python_function(n, fixed))


if __name__ == "__main__":
    unittest.main()
