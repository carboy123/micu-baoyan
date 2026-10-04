#!/usr/bin/env python3
"""从获准使用的“按院校整理”目录生成面经。默认只读检查，--write 写入。

不读取原问卷；只解析院校正文、单份多校记录与待核记录。源路径、行号和
文件哈希仅保存到 .runtime 私有审计。旧 recordId 与文章路径保持不变。
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import html
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = r"(?:M\d{3}|Q2026-\d{3})"
BLOCK = re.compile(rf"^### ({SOURCE_ID}) · ([^\n]+)\n([\s\S]*?)(?=^<a id=\"(?:m\d{{3}}|q2026-\d{{3}})\"|^## \d{{4}} 年保研|\Z)", re.M)
QUESTION = re.compile(r"^\*\*(\d+)、([^\n]+)\*\*\s*\n([\s\S]*?)(?=^\*\*\d+、|^未填写的题号|^问卷标记为|\Z)", re.M)
HELD = {"Q2026-001", "Q2026-002"}
MULTI_SCHOOLS = ["山东大学", "苏州大学", "长安大学"]
GROUPS = (
    ("申请概况", range(1, 6)), ("进面与考核观察", range(6, 8)),
    ("考核安排", range(8, 12)), ("笔试与机试", range(12, 16)),
    ("英语环节", range(16, 18)), ("专业课环节", range(18, 21)),
    ("科研、项目与竞赛", range(21, 24)), ("个人感受与建议", range(24, 28)),
)
PRIVATE_PATTERNS = (
    (r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)", "[联系方式已移除]"),
    (r"(?i)[A-Z0-9_.+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "[邮箱已移除]"),
    (r"(?i)(?:微信号?|wechat|\bqq\b|\bwx\b|\bvx\b)\s*[:：=]\s*[A-Z0-9_-]+", "[联系方式已移除]"),
    (r"(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?![\d.])", "[网络地址已移除]"),
    (r"https?://[^\s<>）)]+", "[外部链接已移除]"),
)


def record_id(source_id: str) -> str:
    return "legacy-" + source_id[1:] if source_id.startswith("M") else "survey-2026-" + source_id.rsplit("-", 1)[1]


def record_path(source_id: str, root: Path) -> Path:
    folder = "legacy" if source_id.startswith("M") else "survey-2026"
    return root / "content" / "experiences" / "archive" / folder / (record_id(source_id) + ".md")


def clean_markdown(value: str, source_id: str, privacy_edits: list) -> str:
    original = value
    for pattern, replacement in PRIVATE_PATTERNS:
        value = re.sub(pattern, replacement, value)
    if value != original:
        privacy_edits.append({"sourceId": source_id, "action": "移除直接联系信息、网络地址或外链"})
    # 原文 <br> 转为 Markdown 换行，兼容关闭原始 HTML 的生产配置。
    value = re.sub(r"<br\s*/?>\s*\n?", lambda _: "\\\n", value, flags=re.I)
    value = re.sub(r"<[^>\n]+>", lambda match: html.escape(match[0]), value)
    value = value.replace("{{", "&#123;&#123;")
    value = re.sub(r"(?m)^[^\S\r\n]+$", "", value)
    return value.strip()


def plain_field(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "；", value, flags=re.I)
    value = value.replace("\\\n", "；")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def stage_name(value: str) -> str:
    if "夏令营" in value and "预推免" in value:
        return "夏令营与预推免"
    return value.removeprefix("其他〖").removesuffix("〗")


def parse_sources(source_dir: Path) -> tuple[list[dict], dict]:
    source_dir = source_dir.resolve()
    files = sorted((source_dir / "院校").glob("*.md")) + [source_dir / "多校合填记录.md", source_dir / "待核实条目.md"]
    context_files = [source_dir / "README.md", source_dir / "整理核对记录.md"]
    if not files or any(not path.is_file() for path in files + context_files):
        raise ValueError("缺少按院校整理目录的院校正文、索引或特殊记录文件")
    audit = {"sourceDirectory": str(source_dir), "files": [], "records": [], "held": [], "privacyEdits": []}
    records = []
    seen = set()
    for path in files + context_files:
        data = path.read_bytes()
        audit["files"].append({"path": str(path.relative_to(source_dir)), "sha256": hashlib.sha256(data).hexdigest()})
        if path in context_files:
            continue
        source = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        for match in BLOCK.finditer(source):
            source_id, title, body = match.groups()
            if source_id in seen:
                raise ValueError(f"源条目重复：{source_id}")
            seen.add(source_id)
            year_match = re.search(r"\*\*申请年份\*\*：(\d{4}) 年保研", body)
            if not year_match:
                raise ValueError(f"条目缺少明确申请年份：{source_id}")
            school = path.stem if path.parent.name == "院校" else ("多校记录" if path.stem == "多校合填记录" else "院校待核实")
            notes = [line.removeprefix("> 整理备注：").strip() for line in body.splitlines() if line.startswith("> 整理备注：")]
            record = {"sourceId": source_id, "title": title, "school": school, "applicationYear": int(year_match[1]), "body": body, "notes": notes}
            if source_id.startswith("M"):
                if "#### 原稿正文\n" not in body:
                    raise ValueError(f"缺少原稿正文：{source_id}")
                record["originalBody"] = body.split("#### 原稿正文\n", 1)[1].strip()
                info = re.search(r"\*\*基本信息\*\*：(20\d{2}届) · (.+?)；本科院校层次：(.+?)；结果：([^\n]+)", record["originalBody"])
                if not info:
                    raise ValueError(f"原稿基本信息格式变化：{source_id}")
                record["originalCohort"], record["stage"], record["undergraduateTier"], record["result"] = info.groups()
                original_school = re.search(r"\*\*原院校标题\*\*：(.+?)。?(?:\n|$)", body)
                record["originalSchool"] = original_school[1].removesuffix("。") if original_school else school
                record["department"] = re.sub(r"（样本 \d+）", "", title).strip()
            else:
                questions = {}
                for question in QUESTION.finditer(body):
                    number = int(question[1])
                    if number in questions or not 1 <= number <= 27:
                        raise ValueError(f"公共问题编号重复或超出范围：{source_id}")
                    questions[number] = {"label": question[2], "answer": question[3].strip()}
                if not {1, 2, 3, 4, 5}.issubset(questions):
                    raise ValueError(f"缺少申请基本信息：{source_id}")
                record["questions"] = questions
                record["originalSchool"] = questions[1]["answer"]
                record["department"] = questions[2]["answer"]
                record["stage"] = questions[3]["answer"]
                record["undergraduateTier"] = questions[4]["answer"]
                record["result"] = questions[5]["answer"]
                record["missingNotes"] = [line for line in body.splitlines() if line.startswith(("未填写的题号：", "问卷标记为“跳过”的题号："))]
            records.append(record)
            audit["records"].append({"sourceId": source_id, "recordId": record_id(source_id), "file": str(path.relative_to(source_dir)), "line": source[:match.start()].count("\n") + 1, "school": school, "applicationYear": record["applicationYear"]})
    expected = {f"M{i:03d}" for i in range(1, 52)} | {f"Q2026-{i:03d}" for i in range(1, 114)}
    if seen != expected:
        raise ValueError(f"源条目集合变化：缺少{sorted(expected - seen)}；新增{sorted(seen - expected)}。请先核对来源对应。")
    return records, audit


def public_notes(record: dict, privacy_edits: list) -> str:
    notes = []
    for original in record["notes"]:
        note = original.replace("按用户确认口径", "按本组申请年份口径")
        note = note.replace("并在三校文件中建立入口；", "")
        note = clean_markdown(note, record["sourceId"], privacy_edits)
        # 关联疑似重复记录时链接实际文章，不展示内部源编号。
        def link_reference(match):
            source_id = match[0]
            path = record_path(source_id, Path("/")).relative_to("/content").as_posix()
            return '[另一份相关记录]({{< relref "/' + path + '" >}})'
        note = re.sub(SOURCE_ID, link_reference, note)
        notes.append("> " + note)
    return "## 阅读提示\n\n" + "\n\n".join(notes) + "\n\n" if notes else ""


def build_records(source_dir: Path, root: Path) -> tuple[dict[Path, str], dict]:
    """返回路径到完整 Markdown 的映射及私有审计；本函数不写文件。"""
    root = root.resolve()
    records, audit = parse_sources(source_dir)
    generated = {}
    public_years = Counter()
    for record in records:
        source_id = record["sourceId"]
        if source_id in HELD:
            if record["originalSchool"] != source_id[-1] or record["department"] != source_id[-1]:
                raise ValueError("数字院校待核记录已变化，请重新审核")
            audit["held"].append({"sourceId": source_id, "reason": "院校与学院仅为数字，没有可识别院校及实质经验"})
            continue
        path = record_path(source_id, root)
        if path.exists():
            existing, _ = json.JSONDecoder().raw_decode(path.read_text(encoding="utf-8-sig"))
            meta = copy.deepcopy(existing)
            if meta.get("params", {}).get("recordId") != record_id(source_id):
                raise ValueError(f"已有路径的 recordId 不一致：{source_id}")
        else:
            meta = {"date": "2026-10-03", "params": {}}
        school = record["school"]
        year = record["applicationYear"]
        department = plain_field(clean_markdown(record["department"], source_id, audit["privacyEdits"]))
        stage = stage_name(plain_field(record["stage"]))
        title = f"{school}｜{department}｜{year}年申请 · {stage}" if school != "多校记录" else f"多校考核回忆｜{year}年申请 · {stage}"
        meta.update({"title": title, "description": f"{year} 年保研申请的一份匿名{school}考核记录，保留当时经历、结果与个人观察。", "type": "experience", "draft": False, "lastmod": "2026-10-05"})
        meta["params"].update({
            "status": "published", "kind": "院校面经", "recordId": record_id(source_id), "sourceId": source_id,
            "school": school, "schools": MULTI_SCHOOLS.copy() if school == "多校记录" else [school],
            "department": department, "direction": "", "stage": stage, "applicationYear": year,
            "cohort": "", "originalCohort": record.get("originalCohort", ""),
            "originalSchool": plain_field(record["originalSchool"]), "author": "匿名投稿", "studentId": "",
            "result": plain_field(record["result"]), "undergraduateTier": plain_field(record["undergraduateTier"]), "sources": [],
        })
        body = public_notes(record, audit["privacyEdits"])
        if source_id.startswith("M"):
            body += "## 当时的申请与考核\n\n" + clean_markdown(record["originalBody"], source_id, audit["privacyEdits"]) + "\n\n"
            body += "原稿年份标注在正文中原样保留；本页按申请年份归组。\n\n"
        else:
            meta["params"]["collectionYear"] = 2026
            for heading, numbers in GROUPS:
                answers = []
                for number in numbers:
                    if number not in record["questions"]:
                        continue
                    question = record["questions"][number]
                    answer = clean_markdown(question["answer"], source_id, audit["privacyEdits"])
                    if answer:
                        answers.append(f"**{number}、{question['label']}**\n\n{answer}")
                if answers:
                    body += f"## {heading}\n\n" + "\n\n".join(answers) + "\n\n"
        body += "{{< studio-credit >}}\n"
        body = re.sub(r"(?m)^[^\S\r\n]+$", "", body)
        if re.search(r"参考资料|\.xlsx|Sheet1|用户确认|\*\*来源\*\*|问卷提交日期|原序号", body):
            raise ValueError(f"公开正文仍包含内部定位信息：{source_id}")
        generated[path] = json.dumps(meta, ensure_ascii=False, indent=2) + "\n\n" + body
        public_years[year] += 1
    audit["summary"] = {"sourceRecords": len(records), "publishedRecords": len(generated), "heldRecords": len(audit["held"]), "publishedByApplicationYear": dict(sorted(public_years.items())), "singleSchoolRecords": sum(r["sourceId"] not in HELD and r["school"] != "多校记录" for r in records), "multiSchoolRecords": sum(r["school"] == "多校记录" for r in records), "privacyEdits": len(audit["privacyEdits"])}
    for source in audit["files"]:
        if hashlib.sha256((source_dir / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("生成期间原始资料发生变化，请重新检查")
    return generated, audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=ROOT / "参考资料" / "按院校整理")
    parser.add_argument("--write", action="store_true", help="写入162篇正文与忽略目录下的审计")
    parser.add_argument("--replace-existing", action="store_true", help="核对人工修改后，明确允许覆盖已有差异")
    args = parser.parse_args()
    generated, audit = build_records(args.source_dir, ROOT)
    changed = [path for path, value in generated.items() if not path.exists() or path.read_text(encoding="utf-8") != value]
    if args.write:
        existing_changes = [path for path in changed if path.exists()]
        if existing_changes and not args.replace_existing:
            raise SystemExit(f"有 {len(existing_changes)} 篇已有面经与本次输出不同，未写入任何内容。请先检查人工修改；确认后使用 --replace-existing。")
        for path in changed:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(generated[path], encoding="utf-8", newline="\n")
        audit_path = ROOT / ".runtime" / "import-audit" / "school-interviews.json"
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"write": args.write, "changedFiles": len(changed), **audit["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
