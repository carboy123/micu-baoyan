"""Check that retired anonymous profiles stay private without losing outcomes.

Uses the real Hugo aggregation and an isolated fixture. With --build, reuse an
existing production build; otherwise build into a fresh ignored test directory.
Historical hashes describe the approved count distributions before retirement,
not page order or wording. New reviewed profiles may add to those snapshots.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


PROJECT = Path(__file__).resolve().parents[1]
BASELINES = {
    "cohort-2026": "49452762e4d17f227b629cf018d68755fea9a3951130941f6cc96703f5602361",
    "cohort-2027": "148207e4bdcb62495c7e8f8305b341ee6c944bb74eb45e4d82f3f136e54ac4af",
}


def distribution(period):
    return {
        "sampleCount": period["sampleCount"],
        "undergraduate": {item["label"]: item["count"] for item in period["undergraduate"]},
        "destination": {item["label"]: item["count"] for item in period["destination"]},
        "schools": {item["name"]: item["count"] for item in period["schools"]},
    }


def run_hugo(executable: str, *args: str) -> None:
    result = subprocess.run([executable, *args], cwd=PROJECT, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)


class PageProbe(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = 0
        self.filter_hidden = None
        self.search_json = []
        self.capture_search = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-student-card" in attrs:
            self.cards += 1
        if "data-student-filters" in attrs:
            self.filter_hidden = "hidden" in attrs
        if tag == "script" and attrs.get("id") == "search-data":
            self.capture_search = True

    def handle_data(self, data):
        if self.capture_search:
            self.search_json.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.capture_search = False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    local_hugo = PROJECT / "tools/hugo/hugo.exe"
    parser.add_argument("--hugo", default=str(local_hugo) if local_hugo.is_file() else "hugo")
    parser.add_argument("--build", type=Path)
    parser.add_argument("--expect-empty", action="store_true", help="Verify this release's intentionally empty student showcase; omit after real reviewed submissions are added")
    args = parser.parse_args()
    data = json.loads((PROJECT / "data/outcomes.json").read_text(encoding="utf-8"))
    source_periods = {period["id"]: period for period in data["periods"]}
    for period_id, expected_hash in BASELINES.items():
        period = source_periods[period_id]
        canonical = json.dumps(distribution(period), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert hashlib.sha256(canonical.encode()).hexdigest() == expected_hash, f"Historical count distribution changed: {period_id}"
        assert not period.get("profileBased"), f"Anonymous historical outcomes require a retained aggregate: {period_id}"
    assert not list((PROJECT / "content/students").glob("student-2027-*/index.md")), "Retired questionnaire profiles must not become public student pages again"

    temporary_root = PROJECT / ".runtime/tests"
    temporary_root.mkdir(parents=True, exist_ok=True)
    fixture = Path(tempfile.mkdtemp(prefix="community-students-", dir=temporary_root))
    (fixture / "layouts/_partials/site").mkdir(parents=True)
    (fixture / "content/students").mkdir(parents=True)
    (fixture / "data").mkdir()
    (fixture / "hugo.toml").write_text("baseURL='https://example.test/'\ndisableKinds=['taxonomy','term','RSS','sitemap']\n", encoding="utf-8")
    (fixture / "content/_index.md").write_text("---\ntitle: Fixture\n---\n", encoding="utf-8")
    (fixture / "layouts/home.html").write_text('{{ partial "site/outcomes-data.html" . | jsonify | safeHTML }}', encoding="utf-8")
    shutil.copy2(PROJECT / "layouts/_partials/site/outcomes-data.html", fixture / "layouts/_partials/site/outcomes-data.html")
    shutil.copy2(PROJECT / "data/outcomes.json", fixture / "data/outcomes.json")

    def aggregate():
        run_hugo(args.hugo, "--source", str(fixture), "--destination", str(fixture / "aggregate"))
        rendered = json.loads((fixture / "aggregate/index.html").read_text(encoding="utf-8"))
        return {period["id"]: period for period in rendered["periods"]}

    actual = aggregate()
    for period_id in BASELINES:
        assert distribution(actual[period_id]) == distribution(source_periods[period_id]), f"Empty student collection lost outcomes: {period_id}"
    assert [actual[key]["sampleCount"] for key in BASELINES] == [64, 82]

    synthetic = {
        "title": "Synthetic reviewed submission", "type": "student", "draft": False,
        "params": {"status": "published", "studentId": "test-reviewed", "countInOutcomes": True,
                   "periodId": "cohort-2027", "school": "Synthetic university", "undergraduateTier": "", "destinationTier": ""},
    }
    (fixture / "content/students/test-reviewed.md").write_text(json.dumps(synthetic) + "\n\nSynthetic fixture only.\n", encoding="utf-8")
    after = aggregate()
    assert distribution(after["cohort-2026"]) == distribution(actual["cohort-2026"])
    assert after["cohort-2027"]["sampleCount"] == 83
    updated = distribution(after["cohort-2027"])
    baseline = distribution(actual["cohort-2027"])
    for dimension in ("undergraduate", "destination"):
        expected = dict(baseline[dimension])
        expected["未提供"] = expected.get("未提供", 0) + 1
        assert updated[dimension] == expected
    assert updated["schools"] == {**baseline["schools"], "Synthetic university": 1}

    build = args.build.resolve() if args.build else fixture / "site"
    if not args.build:
        run_hugo(args.hugo, "--source", str(PROJECT), "--environment", "production", "--buildDrafts=false", "--minify", "--baseURL", "https://example.test/micu-baoyan/", "--destination", str(build))
    assert build.is_dir(), "Production build directory does not exist"
    student_html = (build / "students/index.html").read_text(encoding="utf-8")
    student_probe = PageProbe()
    student_probe.feed(student_html)
    if args.expect_empty:
        assert student_probe.cards == 0, "This release reserves the student display for future reviewed submissions"
    if not student_probe.cards:
        assert student_probe.filter_hidden is True, "Empty student page should not expose unusable filters"
        assert "优秀学员展示正在筹备" in student_html
    assert "/resources/submission/" in student_html, "The contribution entry must remain available"
    assert not list((build / "students").glob("student-2027-*/index.html"))
    for file in list(build.rglob("*.html")) + list(build.rglob("*.xml")):
        assert "/students/student-2027-" not in file.read_text(encoding="utf-8"), f"Retired profile link remains in {file.relative_to(build)}"
    search_probe = PageProbe()
    search_probe.feed((build / "search/index.html").read_text(encoding="utf-8"))
    search = json.loads("".join(search_probe.search_json))
    assert not any("/students/student-2027-" in item.get("url", "") for item in search)
    print("PASS: historical 64/82 and all distributions retained; reviewed new sample can add once; student empty state and contribution entry; retired URLs absent from pages, sitemap, and search")
    print("Isolated fixture: " + str(fixture.relative_to(PROJECT)))


if __name__ == "__main__":
    main()
