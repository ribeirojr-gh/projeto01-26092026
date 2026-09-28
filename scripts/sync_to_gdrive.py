#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated synchronization utility between local project repository
and Google Drive mounted folder.

Target Google Drive location:
GEMINI-APPLICATIONS/UPb-Carbonate-Geochronology-Petrobras
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

# Paths
LOCAL_REPO = Path(__file__).resolve().parent.parent
GDRIVE_ROOT = Path("/run/user/1000/gvfs/google-drive:host=gmail.com,user=ribeirojr.fis/0AJMdF0C-r4sVUk9PVA")
GDRIVE_AGENT_DIR = GDRIVE_ROOT / "1uQiXpQIq6Eql-ILNBtF1Y8bYh1iKT6M_"  # GEMINI-APPLICATIONS
GDRIVE_PROJECT_DIR = GDRIVE_AGENT_DIR / "1PjzFc5gw-cASfGk5XtXzXd3pMz5_yNU-"  # UPb-Carbonate-Geochronology-Petrobras

# Milestone folder mappings (Google Drive folder ID)
FOLDER_MAP = {
    "00_doc": "1_KvT4n8QKom0zZonzQqOTBCxgjUtPsBH",       # 00_documentation_and_audit
    "step00": "10BoOFmpC20NdZ-HEbInC6XElwZr_V-UA",       # step00_environment_setup
    "step01": "1JsTildau9kDdN9LaKyPGDpmaLSspEZT4",       # step01_reference_structures
    "step02": "1GEuk6JFW0hvyjOCRm17LVB4Ep6FqUJc8",       # step02_pristine_convergence
    "step03": "16HKR8eo_waGI03ZkJH-IaCOUaQJto0_2",       # step03_paw_pbesol_benchmark
    "step04A": "1Gazsl_Nn4FAPDHDujCY23o5fhJ_7ggU-",      # step04A_u_pb_paw_validation
    "step04B": "14AjiMCwwCT4cA5GPw7AnrRTsQ83xKDyZ",      # step04B_compounds_uo2_pbco3_uo3
    "step05A": "1oT96x83hcu5S5xHc5f4gB8vZb3j73nNC",      # step05A_host_supercells
    "step05B": "1E7dH69INDVKmMu1i6TRAcUBdoYHDBXPC",      # step05B_pbca_finite_size_gate
    "step05C": "1wU0-0SbErB_odyk6oRBV4jjfzorGa0j_",      # step05C_defect_motifs
    "step06": "1vzaayh4Luvf17x4HazWoCZRe7LG1tynh",       # step06_electronic_oxidation
}


def sync_file_if_changed(src_file: Path, dst_file: Path) -> bool:
    need_copy = False
    if not dst_file.exists():
        need_copy = True
    else:
        try:
            if src_file.stat().st_size != dst_file.stat().st_size:
                need_copy = True
        except Exception:
            need_copy = True

    if need_copy:
        try:
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src_file, dst_file)
            return True
        except Exception as e:
            print(f"[WARN] Failed to copy {src_file.name}: {e}")
            return False
    return False


def sync_documentation():
    dst_folder = GDRIVE_PROJECT_DIR / FOLDER_MAP["00_doc"]
    if not dst_folder.exists():
        print(f"[ERROR] Destination doc folder does not exist: {dst_folder}")
        return

    synced = 0
    # Sync root markdown files
    for fname in ["README.md", "LICENSE", "CITATION.cff", "chat_completo_projeto_datacao_UPb_Petrobras.md"]:
        fpath = LOCAL_REPO / fname
        if fpath.exists():
            if sync_file_if_changed(fpath, dst_folder / fname):
                synced += 1

    # Sync docs/
    docs_dir = LOCAL_REPO / "docs"
    if docs_dir.exists():
        for doc_file in docs_dir.glob("*.md"):
            if sync_file_if_changed(doc_file, dst_folder / doc_file.name):
                synced += 1

    # Sync prompts/
    prompts_dir = LOCAL_REPO / "prompts"
    if prompts_dir.exists():
        dst_prompts = dst_folder / "prompts"
        for pfile in prompts_dir.glob("*.md"):
            if sync_file_if_changed(pfile, dst_prompts / pfile.name):
                synced += 1

    print(f"[SYNC] Documentation & Prompts mirrored ({synced} files updated).")


def sync_step05b():
    dst_folder = GDRIVE_PROJECT_DIR / FOLDER_MAP["step05B"]
    if not dst_folder.exists():
        print(f"[ERROR] Destination step05B folder does not exist: {dst_folder}")
        return

    step_dir = LOCAL_REPO / "step05B_pbca_size_gate"
    if not step_dir.exists():
        return

    synced = 0
    # Copy key JSON and CIF result files directly
    res_dir = step_dir / "resultados_step05B_R3"
    if res_dir.exists():
        for jf in res_dir.glob("*.json"):
            if sync_file_if_changed(jf, dst_folder / jf.name):
                synced += 1
        relax_dir = res_dir / "relax"
        if relax_dir.exists():
            for cf in relax_dir.glob("*.cif"):
                if sync_file_if_changed(cf, dst_folder / cf.name):
                    synced += 1

    # Copy output txt log
    for out_log in step_dir.glob("saida-*.txt"):
        if sync_file_if_changed(out_log, dst_folder / out_log.name):
            synced += 1

    # Create / update compressed archive
    zip_path = LOCAL_REPO / "step05B_pbca_finite_size_gate.zip"
    print(f"[SYNC] Creating compressed archive {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(step_dir):
            # Avoid raw big binaries or temp logs
            files = [f for f in files if not f.endswith((".gpw", ".tmp", ".pyc"))]
            for file in files:
                full_p = Path(root) / file
                rel_p = full_p.relative_to(step_dir)
                z.write(full_p, arcname=str(rel_p))

    if sync_file_if_changed(zip_path, dst_folder / zip_path.name):
        print(f"[SYNC] Updated {zip_path.name} on Google Drive.")
        synced += 1

    # Clean local zip
    zip_path.unlink(missing_ok=True)
    print(f"[SYNC] Step 05B-R3 mirrored ({synced} items updated).")


def sync_step05c():
    dst_folder = GDRIVE_PROJECT_DIR / FOLDER_MAP["step05C"]
    if not dst_folder.exists():
        print(f"[ERROR] Destination step05C folder does not exist: {dst_folder}")
        return

    step_dir = LOCAL_REPO / "step05C_defect_motifs"
    if not step_dir.exists():
        return

    synced = 0
    # Copy key JSON, report and CIF result files directly
    res_dir = step_dir / "results"
    if res_dir.exists():
        for jf in res_dir.glob("*.json"):
            if sync_file_if_changed(jf, dst_folder / jf.name):
                synced += 1
        for rf in res_dir.glob("*.md"):
            if sync_file_if_changed(rf, dst_folder / rf.name):
                synced += 1
        relax_dir = res_dir / "relax"
        if relax_dir.exists():
            for cf in relax_dir.glob("*.cif"):
                if sync_file_if_changed(cf, dst_folder / cf.name):
                    synced += 1

    # Copy prescreened CIFs
    prescreen_dir = step_dir / "structures_prescreened"
    if prescreen_dir.exists():
        dst_pre = dst_folder / "structures_prescreened"
        for cf in prescreen_dir.glob("*.cif"):
            if sync_file_if_changed(cf, dst_pre / cf.name):
                synced += 1

    # Create / update compressed archive
    zip_path = LOCAL_REPO / "step05C_defect_motifs.zip"
    print(f"[SYNC] Creating compressed archive {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(step_dir):
            files = [f for f in files if not f.endswith((".gpw", ".tmp", ".pyc"))]
            for file in files:
                full_p = Path(root) / file
                rel_p = full_p.relative_to(step_dir)
                z.write(full_p, arcname=str(rel_p))

    if sync_file_if_changed(zip_path, dst_folder / zip_path.name):
        print(f"[SYNC] Updated {zip_path.name} on Google Drive.")
        synced += 1

    # Clean local zip
    zip_path.unlink(missing_ok=True)
    print(f"[SYNC] Step 05C mirrored ({synced} items updated).")


def sync_step06():
    dst_folder = GDRIVE_PROJECT_DIR / FOLDER_MAP["step06"]
    if not dst_folder.exists():
        print(f"[ERROR] Destination step06 folder does not exist: {dst_folder}")
        return

    step_dir = LOCAL_REPO / "step06_electronic_oxidation"
    if not step_dir.exists():
        return

    synced = 0
    # Copy key reports, json, and png figures
    for ext in ["*.json", "*.md", "*.png", "*.pdf"]:
        for f in step_dir.rglob(ext):
            rel_p = f.relative_to(step_dir)
            target = dst_folder / rel_p
            if sync_file_if_changed(f, target):
                synced += 1

    print(f"[SYNC] Step 06 mirrored ({synced} items updated).")


def main():
    if not GDRIVE_PROJECT_DIR.exists():
        print(f"[ERROR] Google Drive project mount not found at {GDRIVE_PROJECT_DIR}")
        print("Please check if GVFS Google Drive is mounted.")
        sys.exit(1)

    print(f"[SYNC] Starting synchronization from {LOCAL_REPO}")
    print(f"[SYNC] Target: GEMINI-APPLICATIONS/UPb-Carbonate-Geochronology-Petrobras")
    sync_documentation()
    sync_step05b()
    sync_step05c()
    sync_step06()
    print("[SYNC] Synchronization completed successfully.")


if __name__ == "__main__":
    main()

