"""Exercise the actual Hugo outcomes partial with isolated synthetic records.

The fixture and build live only in .runtime/tests/. No production content, data,
or public directory is modified. Uses the Python standard library and Hugo.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


PROJECT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    local_hugo = PROJECT / "tools" / "hugo" / "hugo.exe"
    parser.add_argument("--hugo", default=str(local_hugo) if local_hugo.is_file() else "hugo")
    args = parser.parse_args()
    fixture_root = PROJECT / ".runtime" / "tests"
    fixture_root.mkdir(parents=True, exist_ok=True)
    fixture = Path(tempfile.mkdtemp(prefix="outcomes-aggregation-", dir=fixture_root))
    (fixture / "layouts" / "_partials" / "site").mkdir(parents=True)
    (fixture / "content" / "students").mkdir(parents=True)
    (fixture / "data").mkdir()
    (fixture / "hugo.toml").write_text(
        "baseURL='https://example.test/'\ndisableKinds=['taxonomy','term','RSS','sitemap']\n",
        encoding="utf-8",
    )
    (fixture / "content" / "_index.md").write_text("---\ntitle: Fixture\n---\n", encoding="utf-8")
    (fixture / "layouts" / "home.html").write_text(
        '{{ partial "site/outcomes-data.html" . | jsonify | safeHTML }}', encoding="utf-8"
    )
    shutil.copy2(
        PROJECT / "layouts" / "_partials" / "site" / "outcomes-data.html",
        fixture / "layouts" / "_partials" / "site" / "outcomes-data.html",
    )
    periods = [
        {
            "id": "historical", "label": "历史合成测试", "sampleCount": 2, "rawRecords": 2,
            "undergraduate": [{"label": "985", "count": 1}, {"label": "四非", "count": 1}],
            "destination": [{"label": "211", "count": 2}],
            "schools": [{"name": "测试甲大学", "count": 2}],
        },
        {
            "id": "profiles", "label": "档案合成测试", "profileBased": True,
            "sampleCount": 999, "rawRecords": 999,
            "undergraduate": [{"label": "985", "count": 999}], "destination": [], "schools": [],
        },
        {
            "id": "empty", "label": "空批次测试", "sampleCount": 0, "rawRecords": 0,
            "undergraduate": [], "destination": [], "schools": [],
        },
    ]
    (fixture / "data" / "outcomes.json").write_text(
        json.dumps({"periods": periods}, ensure_ascii=False), encoding="utf-8"
    )

    def student(name: str, period: str, **fields: object) -> None:
        params = {
            "status": "published", "countInOutcomes": True, "periodId": period,
            "undergraduateTier": "211", "destinationTier": "985", "school": "测试乙大学",
        }
        draft = fields.pop("draft", False)
        params.update(fields)
        doc = {"title": name, "type": "student", "draft": draft, "params": params}
        (fixture / "content" / "students" / f"{name}.md").write_text(
            json.dumps(doc, ensure_ascii=False) + "\n\n合成测试资料。\n", encoding="utf-8"
        )

    student("append", "historical", undergraduateTier="985", destinationTier="211", school="测试甲大学")
    student("first", "profiles")
    student("second", "profiles")
    student("missing", "profiles", undergraduateTier="", destinationTier="", school="")
    student("draft", "profiles", draft=True)
    student("preview", "profiles", status="preview")
    student("not-counted", "profiles", countInOutcomes=False)
    student("other-period", "not-present")
    result = subprocess.run(
        [args.hugo, "--source", str(fixture), "--destination", str(fixture / "output"), "--buildDrafts"],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    report = json.loads((fixture / "output" / "index.html").read_text(encoding="utf-8"))
    actual = {period["id"]: period for period in report["periods"]}
    historical, profiles, empty = actual["historical"], actual["profiles"], actual["empty"]
    def nonzero(items: list[dict]) -> dict:
        return {item["label"]: item["count"] for item in items if item["count"]}
    assert historical["sampleCount"] == 3, historical
    assert nonzero(historical["undergraduate"]) == {"985": 2, "四非": 1}, historical
    assert nonzero(historical["destination"]) == {"211": 3}, historical
    assert historical["schools"] == [{"name": "测试甲大学", "count": 3}], historical
    assert profiles["sampleCount"] == 3, profiles
    assert nonzero(profiles["undergraduate"]) == {"211": 2, "未提供": 1}, profiles
    assert nonzero(profiles["destination"]) == {"985": 2, "未提供": 1}, profiles
    assert {item["name"]: item["count"] for item in profiles["schools"]} == {"测试乙大学": 2, "未明确院校": 1}, profiles
    assert empty["sampleCount"] == 0, empty
    for period in report["periods"]:
        for dimension in ["undergraduate", "destination"]:
            assert [item["label"] for item in period[dimension]] == ["985", "211", "双一流", "四非", "未提供"], (period["id"], dimension)
        for dimension in ["undergraduate", "destination", "schools"]:
            assert sum(item["count"] for item in period[dimension]) == period["sampleCount"], (period["id"], dimension)
    print("PASS: historical + profiles; profile-only aggregation; unknowns; draft/status/count/period exclusions; empty period; common denominator")
    print("Isolated fixture: " + str(fixture.relative_to(PROJECT)))


if __name__ == "__main__":
    main()
