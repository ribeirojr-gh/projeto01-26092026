#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

from gpaw import __version__ as gpaw_version, setup_paths
from gpaw.atom.configurations import configurations, parameters as old_parameters
from gpaw.atom import generator2

from config_step04 import RESULTS_DIR

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def files_for(symbol: str, xc: str):
    out = []
    names = [f"{symbol}.{xc}", f"{symbol}.{xc}.gz"]
    for d in setup_paths:
        p = Path(d)
        for name in names:
            q = p / name
            if q.exists():
                out.append(str(q.resolve()))
    return out


rows = []
for symbol in ("Pb", "U"):
    for xc in ("PBE", "PBEsol"):
        matches = files_for(symbol, xc)
        rows.append({
            "element": symbol,
            "xc": xc,
            "installed_setup_found": bool(matches),
            "installed_setup_paths": ";".join(matches),
        })

with (RESULTS_DIR / "inventario_setups_instalados.csv").open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

Z_U = 92
Z_PB = 82

u_default_e = int(generator2.default[Z_U])
pb_default_e = int(generator2.default[Z_PB])

# IMPORTANT:
# gpaw.setup_paths may contain pathlib.Path/PosixPath objects.
# Convert every entry explicitly to str before JSON serialization.
setup_paths_serializable = [str(Path(p)) for p in setup_paths]

report = {
    "gpaw_version": str(gpaw_version),
    "setup_paths": setup_paths_serializable,
    "old_generator": {
        "Pb_has_atomic_configuration": bool("Pb" in configurations),
        "U_has_atomic_configuration": bool("U" in configurations),
        "Pb_has_default_generation_parameters": bool("Pb" in old_parameters),
        "U_has_default_generation_parameters": bool("U" in old_parameters),
    },
    "generator2": {
        "Pb_default_valence_electrons": pb_default_e,
        "U_default_valence_electrons": u_default_e,
        "Pb_parameter_key": f"Pb{pb_default_e}",
        "U_parameter_key": f"U{u_default_e}",
        "Pb_parameter_entry_exists": bool(
            f"Pb{pb_default_e}" in generator2.parameters
        ),
        "U_parameter_entry_exists": bool(
            f"U{u_default_e}" in generator2.parameters
        ),
        "Pb_parameter_entry": repr(
            generator2.parameters.get(f"Pb{pb_default_e}")
        ),
        "U_parameter_entry": repr(
            generator2.parameters.get(f"U{u_default_e}")
        ),
    },
    "policy": {
        "Pb": (
            "Validar gpaw-setup PBE gerado contra PAW-PBE oficial; "
            "gerar PBEsol com o mesmo old generator."
        ),
        "U": (
            "Nao ha setup U no conjunto oficial instalado. O old generator "
            "possui configuracao atomica de U, mas nao parametros default de "
            "geracao. Usar generator2/dataset U14 apenas como candidato, "
            "exigindo check_all + validacao posterior em compostos antes de "
            "producao."
        ),
    },
}

with (RESULTS_DIR / "auditoria_geradores.json").open(
    "w", encoding="utf-8"
) as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("=" * 80)
print("STEP 04A — AUDITORIA DE PAWs U/Pb")
print("=" * 80)
print("GPAW:", gpaw_version)
print(
    "Old generator: Pb parameters =",
    report["old_generator"]["Pb_has_default_generation_parameters"],
)
print(
    "Old generator: U parameters  =",
    report["old_generator"]["U_has_default_generation_parameters"],
)
print("Generator2 Pb default e-     =", pb_default_e)
print("Generator2 U default e-      =", u_default_e)
print("Generator2 U entry           =", report["generator2"]["U_parameter_entry"])

for row in rows:
    print(
        f"Installed {row['element']}.{row['xc']}: "
        f"{'YES' if row['installed_setup_found'] else 'NO'} "
        f"{row['installed_setup_paths']}"
    )

print("Audit JSON:", RESULTS_DIR / "auditoria_geradores.json")
print("=" * 80)
