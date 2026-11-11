#!/usr/bin/env python3
"""Validate each JSONL benchmark row with the Pydantic model."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pydantic import ValidationError
from fitevidence.schemas.user_profile import BenchmarkCase


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="data/evaluation/benchmark_v1.jsonl")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        print(f"No existe el fichero: {path}")
        return 2
    seen: set[str] = set()
    errors = 0
    rows = 0
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        rows += 1
        try:
            case = BenchmarkCase.model_validate(json.loads(line))
            if case.case_id in seen:
                raise ValueError(f"case_id duplicado: {case.case_id}")
            seen.add(case.case_id)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            errors += 1
            print(f"Línea {line_no}: {exc}")
    print(f"Filas: {rows} | IDs únicos: {len(seen)} | Errores: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
