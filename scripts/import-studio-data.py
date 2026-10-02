#!/usr/bin/env python3
"""将获准发布的工作室问卷整理为 Hugo 内容；原件只读，不参与网站构建。

默认仅检查；显式传入 --write 才写入公开内容和 .runtime/ 下的私有审计。
仅用 Python 标准库。公开文件从允许字段生成，绝不复制整张问卷。
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
EMPTY = {"", "(空)", "（空）", "(跳过)", "（跳过）", "无", "暂无", "没有", "无。", "无感言", "无感言。", "/", "-", "。"}
TIERS = ("985", "211", "双一流", "四非", "未提供")
UNKNOWN_SCHOOL = "未明确院校"
# 通用简称只做无歧义映射；去向表的简称结合原行业务内容单独核对。
ALIASES = {
    "西湖": "西湖大学", "天大": "天津大学", "北理工": "北京理工大学",
    "北航": "北京航空航天大学", "上交": "上海交通大学", "北邮": "北京邮电大学",
    "西交": "西安交通大学", "西电": "西安电子科技大学", "南航": "南京航空航天大学",
    "南开": "南开大学", "厦大": "厦门大学", "复旦": "复旦大学", "中南": "中南大学",
    "苏大": "苏州大学", "华电": "华北电力大学", "华理": "华东理工大学",
    "哈工大": "哈尔滨工业大学", "哈工程": "哈尔滨工程大学", "大连理工": "大连理工大学",
    "西南交大": "西南交通大学", "西南交通": "西南交通大学", "中海洋": "中国海洋大学",
    "中科大": "中国科学技术大学", "东南": "东南大学", "重大": "重庆大学",
    "国防科大": "国防科技大学", "上科大": "上海科技大学", "成电": "电子科技大学",
    "电子科大": "电子科技大学", "国科大杭高院": "中国科学院大学", "北京邮电": "北京邮电大学",
}
SCHOOLS = (
    "中国科学院微小卫星创新研究院", "北京航空航天大学", "北京理工大学", "北京交通大学",
    "北京邮电大学", "北京科技大学", "北京师范大学", "中国科学技术大学", "中国科学院大学",
    "南京航空航天大学", "南京理工大学", "南京邮电大学", "南京师范大学", "哈尔滨工业大学",
    "哈尔滨工程大学", "华中科技大学", "华北电力大学", "华东理工大学", "华东师范大学",
    "华南理工大学", "西安电子科技大学", "西安交通大学", "西南交通大学", "西北工业大学",
    "电子科技大学", "国防科技大学", "上海交通大学", "上海科技大学", "中国海洋大学",
    "中国农业大学", "中央民族大学", "中国地质大学", "中国矿业大学", "合肥工业大学",
    "南方科技大学", "大连理工大学", "清华大学", "北京大学", "复旦大学", "南京大学",
    "天津大学", "同济大学", "东南大学", "东北大学", "湖南大学", "湖北大学", "厦门大学", "山东大学",
    "重庆大学", "四川大学", "中南大学", "中山大学", "浙江大学", "深圳大学", "苏州大学",
    "上海大学", "南开大学", "南昌大学", "兰州大学", "吉林大学", "江南大学", "东华大学", "西湖大学",
)
SOURCES = {
    "outcomes2025": "331845937_按文本_2025米醋电子工作室保研去向_64_64.xlsx",
    "outcomes2027": "386398386_按文本_米醋电子工作室2027推免去向_83_83.xlsx",
    "interviews2026": "386469381_按文本_2026米醋电子工作室保研面经收集问卷_113_113.xlsx",
    "interviewsLegacy": "2026-8-7 米醋电子工作室保研面经整理 231938.md",
}
# 已人工核验：两条只有数字院校/学院且无实质经验，不公开为真实面经。
HELD_INTERVIEWS = {1: "院校及学院仅填数字1，无实质经验", 2: "院校及学院仅填数字2，无实质经验"}
EXCLUDED_OUTCOMES_2027 = {51: 50}
PUBLICATION_DATE = "2026-10-02"
# 2026-10-03 核对：仅适用于指定原始记录，不能据此匹配作者或批量推断其他问卷。
# 中国地质大学由用户确认，不区分武汉、北京；其余据同一行去向、offer及院校上下文。
REVIEWED_DESTINATIONS = {
    (2025, 29): ("湖大", "湖南大学"),
    (2025, 53): ("电科直博", "电子科技大学"),
    (2025, 55): ("湖大人机院", "湖南大学"),
    (2027, 6): ("控制工程", "中国地质大学"),
    (2027, 21): ("电科深", "电子科技大学"),
    (2027, 54): ("电科", "电子科技大学"),
    (2027, 67): ("南京邮电大大学集成电路", "南京邮电大学"),
    (2027, 69): ("北理珠", "北京理工大学"),
}


def read_xlsx(path: Path) -> list[list[str]]:
    """只读第一张工作表，同时支持共享字符串、内联字符串与普通值。"""
    with ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(n.itertext()) for n in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", NS)]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in sheet.findall("m:sheetData/m:row", NS):
            result = []
            for cell in row.findall("m:c", NS):
                letters = re.match(r"[A-Z]+", cell.attrib["r"])[0]
                index = 0
                for letter in letters:
                    index = index * 26 + ord(letter) - 64
                while len(result) < index:
                    result.append("")
                value = cell.find("m:v", NS)
                if cell.attrib.get("t") == "s":
                    result[index - 1] = strings[int(value.text)] if value is not None else ""
                elif cell.attrib.get("t") == "inlineStr":
                    inline = cell.find("m:is", NS)
                    result[index - 1] = "".join(inline.itertext()) if inline is not None else ""
                else:
                    result[index - 1] = value.text if value is not None and value.text else ""
            rows.append(result)
        width = max(map(len, rows))
        return [r + [""] * (width - len(r)) for r in rows]


def text(value: object) -> str:
    value = str(value or "").strip()
    return "" if value in EMPTY else value


def school_name(value: str) -> str:
    # 多校合填不能拆成若干独立经历。
    if value.strip() == "山东大学 苏州大学 长安大学":
        return "多校记录"
    for school in sorted(SCHOOLS, key=len, reverse=True):
        if value.startswith(school):
            return school
    for alias in sorted(ALIASES, key=len, reverse=True):
        if value.startswith(alias):
            return ALIASES[alias]
    return UNKNOWN_SCHOOL


def outcome_school(source_year: int, record: int, value: str) -> str:
    reviewed = REVIEWED_DESTINATIONS.get((source_year, record))
    if reviewed:
        expected, school = reviewed
        if value != expected:
            raise ValueError(f"去向表 {source_year} 第 {record} 条原填内容变化，须重新核对简称映射")
        return school
    return school_name(value)


def privacy_clean(value: str, audit: list, reference: str) -> str:
    """阻止直接联系方式和链接进入投稿正文；不根据IP、昵称推断身份。"""
    value = text(value)
    patterns = (
        (r"https?://[^\s<>）)]+", "[外部链接已移除]"),
        (r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[邮箱已移除]"),
        (r"(?<!\d)1[3-9]\d{9}(?!\d)", "[联系方式已移除]"),
        (r"(?i)(?:微信号?|wechat|\bqq\b|\bwx\b|\bvx\b)\s*[:：=]\s*[A-Za-z0-9_-]+", "[联系方式已移除]"),
    )
    original = value
    for pattern, replacement in patterns:
        value = re.sub(pattern, replacement, value)
    if original != value:
        audit.append({"reference": reference, "action": "移除直接联系信息或外部链接"})
    return value.replace("┋", "、")


def stage_name(value: str) -> str:
    if "夏令营" in value and "预推免" in value:
        return "夏令营与预推免"
    if value.startswith("其他〖"):
        return value.removeprefix("其他〖").removesuffix("〗")
    return value


def content_file(title: str, description: str, kind: str, params: dict, body: str) -> str:
    frontmatter = {
        "title": title, "description": description, "type": kind,
        "date": PUBLICATION_DATE, "draft": False, "params": {"status": "published", **params},
    }
    # 清理纯空白行，保留非空行末用于 Markdown 换行的双空格。
    body = re.sub(r"(?m)^[^\S\r\n]+$", "", body)
    return json.dumps(frontmatter, ensure_ascii=False, indent=2) + "\n\n" + body.strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="写入公开整理内容及私有审计；默认仅检查")
    parser.add_argument("--replace-existing", action="store_true", help="明确允许覆盖已有整理文件；需先核对人工修改")
    parser.add_argument("--add-only", action="store_true", help="只新增缺失的公开文件，保留全部已有文件，并更新私有审计")
    parser.add_argument("--source-dir", type=Path, default=ROOT / "参考资料")
    args = parser.parse_args()
    if args.replace_existing and args.add_only:
        parser.error("--replace-existing 与 --add-only 不可同时使用")
    source_paths = {key: args.source_dir / value for key, value in SOURCES.items()}
    hashes_before = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in source_paths.items()}
    audit = {"created": PUBLICATION_DATE, "sources": [{"key": key, "file": str(path), "sha256": hashes_before[key]} for key, path in source_paths.items()], "normalization": [], "duplicates": [], "privacyEdits": [], "heldInterviews": [], "studentMappings": [], "reflectionMappings": [], "omittedReflections": []}
    generated = {}
    periods = []
    all_outcome_records = []
    for year in (2025, 2027):
        rows = read_xlsx(source_paths[f"outcomes{year}"])[1:]
        assert len(rows) == (64 if year == 2025 else 83), "去向表数量变化，需要重新人工审核后再导入"
        under_i, dest_i, final_i = (6, 7, 9) if year == 2025 else (8, 9, 11)
        graduation_year = 2026 if year == 2025 else 2027
        period_id = f"cohort-{graduation_year}"
        cleaned = []
        for index, row in enumerate(rows, 1):
            assert row[0] == str(index), "问卷序号变化，禁止按旧行映射导入"
            if year == 2027 and index in EXCLUDED_OUTCOMES_2027:
                kept = EXCLUDED_OUTCOMES_2027[index]
                assert row[6:] == rows[kept - 1][6:], "已确认重复的回答发生变化，需要重新审核"
                audit["duplicates"].append({"source": "outcomes2027", "record": index, "keptRecord": kept, "action": "exclude", "reason": "昵称、联系方式及所有业务回答完全一致，仅提交元数据不同"})
                continue
            raw_school = text(row[final_i])
            school = outcome_school(year, index, raw_school)
            audit["normalization"].append({"source": f"outcomes{year}", "record": index, "rawDestination": raw_school, "school": school})
            record = {"periodId": period_id, "sourceRecord": index, "undergraduate": text(row[under_i]) or "未提供", "destination": text(row[dest_i]) or "未提供", "school": school}
            assert record["undergraduate"] in TIERS and record["destination"] in TIERS
            cleaned.append(record)
            if year == 2025:
                reflection = privacy_clean(row[10], audit["privacyEdits"], f"outcomes2025:{index}:reflection")
                if reflection and not reflection.isdecimal() and re.search(r"[\w\u4e00-\u9fff]", reflection):
                    record_id = f"reflection-2025-{index:03d}"
                    params = {
                        "kind": "上岸感言", "recordId": record_id, "studentId": "",
                        "applicationYear": 2025, "periodId": period_id, "school": school,
                        "department": "", "direction": "", "stage": "", "cohort": "2026届",
                        "author": "匿名投稿", "result": "问卷自报", "sources": [],
                    }
                    title = f"2026届申请感言 · 匿名记录 {index:02d}"
                    description = reflection[:90] + ("…" if len(reflection) > 90 else "")
                    body = "## 个人感言\n\n" + html.escape(reflection)
                    body += "\n\n毕业届别：2026 届。以上为投稿者的个人感受。\n\n米醋电子工作室 · 匿名学员投稿整理。"
                    generated[ROOT / "content" / "experiences" / "archive" / "reflections-2025" / f"{record_id}.md"] = content_file(title, description, "experience", params, body)
                    audit["reflectionMappings"].append({"recordId": record_id, "source": "outcomes2025", "record": index, "sourceRow": index + 1})
                else:
                    audit["omittedReflections"].append({"source": "outcomes2025", "record": index, "reason": "未提供感言或仅空白、跳过、无效占位"})
            if year == 2027:
                student_id = f"student-2027-{index:03d}"
                display_name = f"米醋学员 27-{index:03d}"
                reflection = privacy_clean(row[12], audit["privacyEdits"], f"outcomes2027:{index}:reflection")
                if len(reflection) <= 1 or reflection.isdecimal():
                    reflection = ""
                # 新档案不用昵称、身份、联系方式推断公开展示名或关联面经。
                admission_type = "直博" if "直博" in raw_school else ("专硕" if "专硕" in raw_school else "")
                params = {
                    "studentId": student_id, "displayName": display_name, "featured": False,
                    "cohort": "2027届", "applicationYear": "", "undergraduateTier": record["undergraduate"],
                    "school": school, "department": "", "direction": "", "admissionType": admission_type,
                    "result": "问卷自报", "periodId": period_id, "destinationText": raw_school,
                    "destinationTier": record["destination"], "countInOutcomes": True,
                    "hasReflection": bool(reflection),
                }
                body = "## 去向与背景\n\n"
                body += f"- 届次：2027 届。\n- 本科院校层次：{record['undergraduate']}（问卷原选项）。\n"
                body += f"- 最终去向（原填）：{html.escape(raw_school) or '未提供'}。\n- 结果状态：问卷自报。\n"
                if year == 2027 and index == 6:
                    body += "- 核对后的去向院校：中国地质大学，暂不区分校区。\n"
                if school == UNKNOWN_SCHOOL:
                    body += "\n原填信息不足以明确院校，暂不推断学校、学院或培养类型。\n"
                body += "\n## 上岸感言\n\n" + (html.escape(reflection) if reflection else "这份记录暂未提供可展示的感言。")
                generated[ROOT / "content" / "students" / student_id / "index.md"] = content_file(display_name, f"2027 届匿名学员的本科院校层次、问卷自报去向与感言。", "student", params, body)
                audit["studentMappings"].append({"studentId": student_id, "source": "outcomes2027", "record": index, "originalNickname": row[6], "sourceRow": index + 1, "experienceLinks": []})
        if year == 2025:
            # 缺少稳定身份字段：相同业务回答只标疑似重复，不直接删除样本。
            groups = defaultdict(list)
            for i, row in enumerate(rows, 1):
                groups[tuple(row[6:])].append(i)
            for indexes in groups.values():
                if len(indexes) > 1:
                    audit["duplicates"].append({"source": "outcomes2025", "records": indexes, "action": "retain_pending_review", "reason": "业务回答相同，但无身份字段，不能确认为同一个人"})
        undergraduate = Counter(r["undergraduate"] for r in cleaned)
        destination = Counter(r["destination"] for r in cleaned)
        schools = Counter(r["school"] for r in cleaned)
        schools.setdefault(UNKNOWN_SCHOOL, 0)
        if year == 2025:
            note = "本科 2026 届（2022 级），2025 年保研申请；按 64 份问卷记录统计。"
        else:
            note = "本科 2027 届；申请年份未单独提供。已排除一份完全重复的提交。"
        period = {"id": period_id, "label": f"{graduation_year} 届", "applicationYear": 2025 if year == 2025 else None, "graduationYear": graduation_year, "rawRecords": len(rows), "sampleCount": len(cleaned), "excludedCount": len(rows) - len(cleaned), "note": note, "undergraduate": [{"label": t, "count": undergraduate[t]} for t in TIERS], "destination": [{"label": t, "count": destination[t]} for t in TIERS], "schools": [{"name": name, "count": count} for name, count in sorted(schools.items(), key=lambda pair: (-pair[1], pair[0]))]}
        period["profileBased" if year == 2027 else "aggregateOnly"] = True
        for field in ("undergraduate", "destination", "schools"):
            assert sum(item["count"] for item in period[field]) == len(cleaned)
        periods.append(period)
        all_outcome_records.extend(cleaned)
    generated[ROOT / "data" / "outcomes.json"] = json.dumps({"periods": periods}, ensure_ascii=False, indent=2) + "\n"

    original = source_paths["interviewsLegacy"].read_text(encoding="utf-8-sig")
    legacy_count = 0
    current_school = ""
    for match in re.finditer(r"^(#{2,3}) (.+)\n([\s\S]*?)(?=^#{2,3} |\Z)", original, flags=re.M):
        level, heading, body = match.groups()
        if level == "##":
            current_school = re.sub(r"^\d+\.\s*", "", heading).strip()
            continue
        legacy_count += 1
        record_id = f"legacy-{legacy_count:03d}"
        info = re.search(r"\*\*基本信息\*\*：([^\n]+)", body)
        assert info, f"旧面经缺少基本信息：{record_id}"
        parts = re.match(r"(20\d{2}届) · (.+?)；本科院校层次：(.+?)；结果：(.+)", info[1])
        assert parts, f"旧面经基本信息格式变化：{record_id}"
        cohort, stage, undergraduate_tier, result = parts.groups()
        body = privacy_clean(body, audit["privacyEdits"], record_id)
        # 只移除文件级分隔线；原有问题与回答、限定语和建议均保留。
        body = re.sub(r"\n---\s*$", "", body).strip()
        body = "## 这次申请\n\n" + body
        body += "\n\n## 阅读说明\n\n以上为投稿者对一次申请或考核的回忆，门槛与偏好为个人观察。原文只提供届次，未将其换算为申请年份。\n\n© 2026 米醋电子工作室 [svip.micu.wiki](https://svip.micu.wiki/) · 保留所有权利。\"米醋电子工作室\"名称及Logo为米醋电子工作室的品牌标识；未经许可，不得移除或篡改本文档中的署名、版权声明与品牌标识。"
        department = re.sub(r"（样本 \d+）", "", heading).strip()
        params = {"kind": "院校面经", "school": current_school, "department": department, "direction": "", "stage": stage_name(stage), "applicationYear": "", "cohort": cohort, "author": "匿名投稿", "recordId": record_id, "studentId": "", "result": result, "undergraduateTier": undergraduate_tier, "sources": []}
        title = f"{current_school}｜{department}｜{cohort} · {stage_name(stage)}"
        generated[ROOT / "content" / "experiences" / "archive" / "legacy" / f"{record_id}.md"] = content_file(title, f"匿名投稿的{current_school}考核回忆，涵盖原文提供的考核环节与个人建议。", "experience", params, body)
    assert legacy_count == 51

    rows = read_xlsx(source_paths["interviews2026"])[1:]
    assert len(rows) == 113
    groups = (
        ("申请概况", [(10, "本科院校层次"), (11, "这次申请的结果"), (12, "进面门槛（个人观察）"), (13, "强 / 弱 com（个人判断）")]),
        ("考核安排", [(14, "考核模块"), (15, "主要面试形式"), (16, "单人面试时长"), (17, "综合面试环节")]),
        ("笔试与机试", [(18, "笔试题型"), (19, "具体笔试题目"), (20, "机试内容"), (21, "具体机试题目")]),
        ("英语环节", [(22, "英语形式"), (23, "英语问题或翻译内容")]),
        ("专业课环节", [(24, "专业课范围"), (25, "专业课提问方式"), (26, "具体专业课问题")]),
        ("科研、项目与竞赛", [(27, "被追问的方面"), (28, "具体追问内容"), (29, "PPT 汇报要求")]),
        ("个人复盘与建议", [(30, "整体难度（个人感受）"), (31, "老师风格（个人感受）"), (32, "项目更看重的因素（个人判断）"), (33, "给后来者的建议")]),
    )
    survey_count = 0
    for index, row in enumerate(rows, 1):
        assert row[0] == str(index)
        if index in HELD_INTERVIEWS:
            assert row[7] == row[8] == str(index), "待核记录变化，需要重新人工审核"
            audit["heldInterviews"].append({"source": "interviews2026", "record": index, "reason": HELD_INTERVIEWS[index]})
            continue
        survey_count += 1
        record_id = f"survey-2026-{index:03d}"
        school = school_name(text(row[7]))
        raw_school = privacy_clean(row[7], audit["privacyEdits"], record_id + ":school")
        department = privacy_clean(row[8], audit["privacyEdits"], record_id + ":department")
        stage = stage_name(text(row[9]))
        audit["normalization"].append({"source": "interviews2026", "record": index, "rawSchool": row[7], "school": school})
        body = "## 记录范围\n\n"
        body += f"- 院校（原填）：{html.escape(raw_school)}。\n- 学院 / 专业 / 方向（原填）：{html.escape(department) or '未提供'}。\n- 参加批次：{html.escape(text(row[9]))}。\n"
        if school == "多校记录":
            body += "\n本条将多个院校的经历合并填报，原文未逐项说明归属，因此保留为一份多校回忆；不能把下列每道题分别归到其中某一所学校。\n"
        if school == UNKNOWN_SCHOOL:
            body += "\n院校名称尚待核实，保留原填文字，不擅自纠正或补全。\n"
        body += "\n问卷于 2026 年收集，未单独提供考核年份与届次；以下内容保留当时回忆及个人观察。\n"
        for heading, fields in groups:
            answers = []
            for column, label in fields:
                answer = privacy_clean(row[column], audit["privacyEdits"], f"{record_id}:{column}")
                if answer:
                    answers.append(f"### {label}\n\n{html.escape(answer)}")
            if answers:
                body += "\n## " + heading + "\n\n" + "\n\n".join(answers) + "\n"
        body += "\n## 阅读说明\n\n未展示的环节表示这份投稿未提供可用回答，不据此认定院校没有该环节。个人观察与经历不代表当年招生规定。\n\n米醋电子工作室 · 匿名学员投稿整理。"
        params = {"kind": "院校面经", "school": school, "department": department, "direction": "", "stage": stage, "applicationYear": "", "cohort": "", "collectionYear": 2026, "author": "匿名投稿", "recordId": record_id, "studentId": "", "result": text(row[11]), "undergraduateTier": text(row[10]), "sources": []}
        title = ("多校考核回忆" if school == "多校记录" else school) + f"｜{department}｜{stage}"
        generated[ROOT / "content" / "experiences" / "archive" / "survey-2026" / f"{record_id}.md"] = content_file(title, f"匿名投稿的{school}申请与考核回忆；考核年份未提供，保留个人经验和结果状态。", "experience", params, body)
    assert survey_count == 111
    assert len(audit["studentMappings"]) == 82
    assert [p["sampleCount"] for p in periods] == [64, 82]
    audit["outcomeRecords"] = all_outcome_records
    reflection_count = len(audit["reflectionMappings"])
    assert reflection_count + len(audit["omittedReflections"]) == 64
    audit["summary"] = {"legacyExperiences": legacy_count, "surveyRawRecords": len(rows), "surveyExperiences": survey_count, "heldSurveyRecords": len(HELD_INTERVIEWS), "publicInterviewExperiences": legacy_count + survey_count, "publicReflections": reflection_count, "omittedReflections": len(audit["omittedReflections"]), "publicExperiences": legacy_count + survey_count + reflection_count, "studentProfiles": len(audit["studentMappings"]), "outcomeSamples": [p["sampleCount"] for p in periods]}
    # 再次直接从原表排除明确重复行计算，独立核对公开三类分布。
    for period, year in zip(periods, (2025, 2027)):
        original_rows = read_xlsx(source_paths[f"outcomes{year}"])[1:]
        valid_rows = [r for n, r in enumerate(original_rows, 1) if not (year == 2027 and n == 51)]
        u, d, f = (6, 7, 9) if year == 2025 else (8, 9, 11)
        assert Counter(text(r[u]) or "未提供" for r in valid_rows) == Counter({i["label"]: i["count"] for i in period["undergraduate"]})
        assert Counter(text(r[d]) or "未提供" for r in valid_rows) == Counter({i["label"]: i["count"] for i in period["destination"]})
        assert Counter(outcome_school(year, int(r[0]), text(r[f])) for r in valid_rows) == Counter({i["name"]: i["count"] for i in period["schools"]})
    hashes_after = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in source_paths.items()}
    assert hashes_before == hashes_after, "原始文件发生变化"
    audit["validation"] = {"originalHashesUnchanged": True, "distributionTotalsMatch": True, "independentRawCountsMatch": True, "studentProfileCountMatches2027Samples": True}
    if args.write:
        changed_existing = [path for path, value in generated.items() if path.exists() and path.read_text(encoding="utf-8") != value]
        if changed_existing and not (args.replace_existing or args.add_only):
            raise SystemExit(f"有 {len(changed_existing)} 个已有文件与本次输出不同。请先检查人工修改；确认后使用 --replace-existing。")
        for path, value in generated.items():
            if args.add_only and path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8", newline="\n")
        audit_path = ROOT / ".runtime" / "import-audit" / "studio-data-2026-10-02.json"
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"write": args.write, "publicFiles": len(generated), **audit["summary"], "validation": audit["validation"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
