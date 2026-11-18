"""Packages Source/ and Report.pdf into the exact submission archive format (Section 5)."""

from __future__ import annotations

from pathlib import Path
import zipfile

from Report.build_report_pdf import TEAM_MEMBERS, build_pdf

SKIP_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache"}


def create_submission_zip() -> Path:
    proj_root = Path(__file__).resolve().parent
    report_pdf = build_pdf()

    student_ids = "_".join(member[0].strip() for member in TEAM_MEMBERS if member[0].strip())
    folder_prefix = student_ids or "StudentID1_StudentID2"
    zip_path = proj_root / f"{folder_prefix}.zip"

    src_dir = proj_root / "Source"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Add Report.pdf under StudentID1_StudentID2_.../Report.pdf
        zf.write(report_pdf, arcname=f"{folder_prefix}/Report.pdf")

        # Add clean Source/ files
        for file_path in sorted(src_dir.rglob("*")):
            if any(part in SKIP_DIRS for part in file_path.parts):
                continue
            if file_path.is_file() and not file_path.name.endswith(".pyc"):
                rel = file_path.relative_to(proj_root).as_posix()
                zf.write(file_path, arcname=f"{folder_prefix}/{rel}")

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"Created submission archive: {zip_path} ({size_mb:.2f} MB)")
    return zip_path


if __name__ == "__main__":
    create_submission_zip()
