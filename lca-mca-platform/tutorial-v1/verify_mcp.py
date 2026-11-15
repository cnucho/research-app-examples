"""Exercise the real MCP tool dispatcher with the released CSV and codebook."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from lca_mca.mcp_tools import ToolWorkspace

from verify import ATTITUDES, CHOICES


def checked(workspace: ToolWorkspace, name: str, arguments: dict) -> dict:
    result = workspace.call(name, arguments)
    if not result.get("ok"):
        raise RuntimeError(f"{name}: {result.get('error_code')}: {result.get('error_message')}")
    return result


def verify(folder: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="lca-mca-tutorial-mcp-") as scratch:
        workspace = ToolWorkspace(Path(scratch))
        output = {}
        for method, question, goal, indicators in (
            ("lca", "응답자의 이동 태도 유형은 무엇인가?", "discover_types", ATTITUDES),
            ("mca", "응답자의 이동 서비스 선택 범주는 어떻게 함께 나타나는가?", "explore_category_relations", CHOICES),
        ):
            brief = {"question_text": question, "goals": [goal], "indicator_candidates": indicators}
            created = checked(workspace, "lca_create_project", {"name": f"tutorial-{method}",
                                                                  "settings": {"research_brief": brief}})
            project_id = created["project_id"]
            imported = checked(workspace, "lca_import_data", {"project_id": project_id,
                                                                "file_handle": str(folder / "mobility_survey.csv"),
                                                                "codebook_handle": str(folder / "codebook.json")})
            assert imported["n_rows"] == 1800 and imported["n_columns"] == 21
            if method == "lca":
                result = checked(workspace, "lca_run_models", {"project_id": project_id,
                                                                "prep_version": 0,
                                                                "class_range": [1, 3],
                                                                "spec": {"indicators": indicators, "n_init": 5,
                                                                         "max_iter": 80, "random_state": 0}})
                output[method] = {"runs": [{"k": run["k"], "success": run["success"]}
                                            for run in result["runs"]]}
                assert any(run["success"] and run["k"] > 1 for run in output[method]["runs"])
            else:
                result = checked(workspace, "lca_run_mca", {"project_id": project_id,
                                                             "prep_version": 0,
                                                             "spec": {"columns": indicators,
                                                                      "n_components": 2}})
                assert result["n_used"] == 1800
                output[method] = {"n_used": result["n_used"], "dimensions": len(result["dimensions"])}
            output[method]["imported_rows"] = imported["n_rows"]
        return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    print(json.dumps(verify(parser.parse_args().folder), ensure_ascii=False, indent=2))
