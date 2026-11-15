"""Build a checked, downloadable tutorial ZIP without fitted results."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


DATA = ("mobility_survey.csv", "mobility_survey.sav", "codebook.json", "item_map.csv")
DOCS = ("README.md", "manual-ko.md", "questionnaire-ko.md")


def package(folder: Path, destination: Path) -> None:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("version") != "tutorial-v1" or manifest.get("synthetic") is not True:
        raise ValueError("Expected the synthetic tutorial-v1 manifest")
    for filename in DATA:
        digest = hashlib.sha256((folder / filename).read_bytes()).hexdigest()
        if digest != manifest["sha256"][filename]:
            raise ValueError(f"Manifest hash mismatch: {filename}")
    source = Path(__file__).resolve().parent
    if destination.exists():
        raise FileExistsError(destination)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for filename in (*DATA, "manifest.json"):
            archive.write(folder / filename, filename)
        for filename in DOCS:
            archive.write(source / filename, filename)
        archive.write(source.parents[1] / "LICENSE-DATA.md", "LICENSE-DATA.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    package(args.folder, args.destination)
