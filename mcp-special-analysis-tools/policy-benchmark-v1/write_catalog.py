"""Record the existing LCA release and generated policy packages in one catalog."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from generate import VERSION, write_json

BASE = "https://github.com/cnucho/research-app-examples"
DOWNLOAD = BASE + "/releases/download/" + VERSION + "/"
SOURCE_ROOT = "mcp-special-analysis-tools/" + VERSION


def catalog(root: Path):
    source = json.loads((root / "user/registry.json").read_text())
    legacy = dict(id="lca-mca.mobility.tutorial-v1", version="1.0.0", title="LCA–MCA synthetic mobility survey",
                  synthetic=True, purpose=["teaching", "application_development", "integration_testing"],
                  source_path="lca-mca-platform/tutorial-v1", formats=["csv", "sav", "json"],
                  entrypoint=BASE + "/releases/download/lca-mca-tutorial-v1/manifest.json",
                  entrypoint_format="legacy_manifest", release=BASE + "/releases/tag/lca-mca-tutorial-v1",
                  resources=[{"name": "mobility_survey", "rows": 1800, "columns": 21,
                              "url": BASE + "/releases/download/lca-mca-tutorial-v1/mobility_survey.csv"}],
                  generation={"seed": 20261115, "version": "tutorial-v1", "real_records_used": False},
                  generator="lca-mca-platform/tutorial-v1/generate.py", license="CC-BY-4.0")
    entries = [legacy]
    for package in source["packages"]:
        p = {k: v for k, v in package.items() if k not in ("metadata_hashes", "resources", "entrypoint", "documentation")}
        p.update(source_path=SOURCE_ROOT, entrypoint=package["entrypoint"], entrypoint_format="frictionless_data_package_v1",
                 distribution={"url": DOWNLOAD + VERSION + "-inputs.zip", "archive_member": package["entrypoint"],
                               "release_manifest": DOWNLOAD + VERSION + "-manifest.json"},
                 package_registry=DOWNLOAD + VERSION + "-registry.json", release=BASE + "/releases/tag/" + VERSION,
                 documentation={"archive_member": package["documentation"], "guide": SOURCE_ROOT + "/manual-ko.md"},
                 generator={"path": SOURCE_ROOT + "/generate.py", "seed": 20261116,
                            "dependencies": SOURCE_ROOT + "/requirements.txt"},
                 resources=package["resources"],
                 integrity={"canonical_csv_hashes": "resources[].hash", "all_asset_hashes": DOWNLOAD + VERSION + "-manifest.json"})
        entries.append(p)
    return dict(schema_version="1.0.0", catalog="research-app-examples", synthetic=True,
                description="Reusable entirely synthetic research inputs. No method recommendation or precomputed answer.",
                repository=BASE, packages=entries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, catalog(args.directory))
    print(args.output)
