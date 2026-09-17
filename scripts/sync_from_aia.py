#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


CRAWLER_FILES = [
    "ALL_files_2.md",
    "all_content_v2.md",
    "cge_content.md",
    "hr_content.md",
    "lc_content.md",
    "oaa_regulations.md",
    "oga_content.md",
    "osa_regulations.md",
    "北大學術單位法規彙整.xlsx",
    "北大行政單位法規彙整.xlsx",
]

HR_DOCUMENTS = [
    "form-11-attendance-leave-request.pdf",
    "form-14-offsite-attendance-sign-sheet.pdf",
    "hr-attendance-faq-11508.docx",
    "new-taipei-labor-standards-leave-qa.pdf",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit(source: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy the approved public AIA knowledge snapshot.")
    parser.add_argument("source", type=Path, help="Path to the ntpu-ai-assistant checkout")
    parser.add_argument("--destination", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    parser.add_argument("--source-commit", default=None)
    args = parser.parse_args()

    source = args.source.resolve()
    destination = args.destination.resolve()
    crawler_destination = destination / "crawler_data"
    hr_destination = destination / "documents" / "hr"
    crawler_destination.mkdir(parents=True, exist_ok=True)
    hr_destination.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for filename in CRAWLER_FILES:
        src = source / "crawler_data" / filename
        if not src.is_file():
            raise SystemExit(f"missing approved source file: {src}")
        dst = crawler_destination / filename
        shutil.copy2(src, dst)
        copied.append(dst)

    for filename in HR_DOCUMENTS:
        src = source / "front_end" / "sports-ai-chat" / "public" / "documents" / "hr" / filename
        if not src.is_file():
            raise SystemExit(f"missing approved source file: {src}")
        dst = hr_destination / filename
        shutil.copy2(src, dst)
        copied.append(dst)

    manifest = {
        "source_repository": "https://github.com/aintpu/ntpu-ai-assistant",
        "source_commit": args.source_commit or git_commit(source),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "approved-public-files-only",
        "files": {
            str(path.relative_to(destination)): {
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(copied)
        },
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"synced {len(copied)} approved public files to {destination}")


if __name__ == "__main__":
    main()

