#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from gpaw import setup_paths
from gpaw.setup_data import SetupData


def inspect(symbol: str, xc: str, setup_dir: str):
    setup_paths.insert(0, str(Path(setup_dir).resolve()))

    # SetupData(..., readxml=True) já lê o XML no construtor.
    # Não chamar read_xml() uma segunda vez.
    data = SetupData(symbol, xc)

    return {
        "symbol": symbol,
        "xc": xc,
        "setup_dir": str(Path(setup_dir).resolve()),
        "Z": float(data.Z),
        "Nv": float(data.Nv),
        "Nc": float(data.Nc),
        "generator_version": (
            None if data.generator_version is None
            else str(data.generator_version)
        ),
        "filename": str(data.filename or ""),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--pb-pbe", required=True)
    p.add_argument("--pb-pbesol", required=True)
    p.add_argument("--u-pbe", required=True)
    p.add_argument("--u-pbesol", required=True)
    args = p.parse_args()

    records = [
        inspect("Pb", "PBE", args.pb_pbe),
        inspect("Pb", "PBEsol", args.pb_pbesol),
        inspect("U", "PBE", args.u_pbe),
        inspect("U", "PBEsol", args.u_pbesol),
    ]

    Path(args.out).write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for record in records:
        print(record)


if __name__ == "__main__":
    main()
