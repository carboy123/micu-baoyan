"""Move public reflections into outcomes without rewriting their body text.

The reviewed input snapshot belongs in .runtime/reflection-migration-input.json.
Use --apply once, then run without it to verify every body and legacy URL alias.
This never reads or changes the original questionnaire workbooks.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    cache = args.cache or root / ".runtime/reflection-migration-input.json"
    snapshot = json.loads(cache.read_text(encoding="utf-8"))
    target_root = (root / "content/outcomes/reflections").resolve()
    legacy_root = (root / "content/experiences/archive/reflections-2025").resolve()
    entries = []
    for entry in snapshot["legacy"]:
        meta = dict(entry["meta"])
        meta["params"] = dict(meta["params"])
        record_id = meta["params"]["recordId"]
        if not re.fullmatch(r"reflection-2025-\d{3}", record_id):
            raise ValueError("Unexpected legacy reflection ID")
        source = (root / entry["source"]).resolve()
        if source.parent != legacy_root or source.suffix != ".md":
            raise ValueError("Legacy source is outside the approved reflection directory")
        alias = "/" + source.relative_to(root / "content").with_suffix("").as_posix() + "/"
        meta["type"] = "reflection"
        meta["aliases"] = list(dict.fromkeys([*meta.get("aliases", []), alias]))
        meta["params"].pop("studentId", None)
        entries.append({**entry, "meta": meta, "target": target_root / "cohort-2026" / (record_id + ".md"), "alias": alias})
    for entry in snapshot["students"]:
        if entry["body"] is None:
            continue
        original = entry["meta"]
        old = original["params"]
        student_id = old["studentId"]
        if not re.fullmatch(r"student-2027-\d{3}", student_id):
            raise ValueError("Unexpected student record ID")
        number = student_id.rsplit("-", 1)[-1]
        record_id = "reflection-2027-" + number
        body = entry["body"]
        plain = re.sub(r"\s+", " ", html.unescape(body.split("## 上岸感言", 1)[1])).strip()
        meta = {
            "title": "2027届申请感言 · 匿名记录 " + str(int(number)).zfill(2),
            "description": plain[:96] + ("…" if len(plain) > 96 else ""),
            "type": "reflection", "date": original.get("date", "2026-10-02"), "draft": False,
            "params": {
                "status": "published", "kind": "上岸感言", "recordId": record_id,
                "applicationYear": old.get("applicationYear", ""), "periodId": "cohort-2027",
                "school": old.get("school", ""), "cohort": "2027届", "author": "匿名投稿",
                "result": "问卷自报", "sources": [],
            },
        }
        entries.append({**entry, "meta": meta, "target": target_root / "cohort-2027" / (record_id + ".md"), "alias": None})
    if len(snapshot["students"]) != 82 or len(snapshot["legacy"]) != 50 or len(entries) != 118:
        raise ValueError("Source counts differ from the reviewed migration scope")
    report = []
    for entry in entries:
        target = entry["target"].resolve()
        if not target.is_relative_to(target_root) or target.suffix != ".md":
            raise ValueError("Target is outside the approved reflection directory")
        expected = json.dumps(entry["meta"], ensure_ascii=False, indent=2) + entry["body"]
        source = (root / entry["source"]).resolve()
        if args.apply:
            if entry["alias"] and source.exists() and hashlib.sha256(source.read_bytes()).hexdigest() != entry["sourceHash"]:
                raise ValueError("Legacy source changed after snapshot; review before migrating")
            if target.exists() and target.read_bytes().decode("utf-8") != expected:
                raise ValueError("Target already contains different content; refusing to overwrite")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(expected.encode("utf-8"))
        actual = target.read_bytes().decode("utf-8")
        meta, end = json.JSONDecoder().raw_decode(actual)
        if actual[end:] != entry["body"] or meta != entry["meta"]:
            raise ValueError("Migrated body or metadata differs from the approved source")
        if entry["alias"] and args.apply and source.exists():
            # Only a checked, individual source file is removed, after the target
            # body and compatibility URL have both been verified.
            if source.parent != legacy_root:
                raise ValueError("Refusing to remove a source outside the legacy directory")
            source.unlink()
        if entry["alias"] and source.exists():
            raise ValueError("Legacy reflection still exists in the experience collection")
        report.append({"source": entry["source"], "target": target.relative_to(root).as_posix(), "alias": entry["alias"], "bodySha256": digest(entry["body"]), "verified": True})
    report_path = root / ".runtime/reflection-migration-report.json"
    if args.apply:
        report_path.write_text(json.dumps({"total": len(report), "cohort2026": 50, "cohort2027": 68, "records": report}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASS: 50 legacy + 68 student reflections; 118 unchanged bodies; 50 legacy aliases; no reflections remain in the experience collection")


if __name__ == "__main__":
    main()
