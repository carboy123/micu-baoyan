"""Validate public student/experience records with Python's standard library.

This reads JSON front matter and the project's simple YAML scalar fields; Hugo
validates the complete YAML during the production build. It does not establish authorship
or consent, and never prints a detected private value into public CI logs.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FIELD = re.compile(r"^( *)([A-Za-z][A-Za-z0-9_]*):\s*(.*?)\s*$")
PRIVATE_FIELDS = {"phone", "phonenumber", "mobile", "mobilenumber", "telephone", "contact", "contactinfo", "wechat", "wechatid", "qq", "email", "privateemail", "contactemail", "ip", "ipaddress", "userid", "idcard", "identitynumber", "studentnumber", "password", "token", "accesstoken"}
PRIVATE_LABEL = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:电话|手机号|联系电话|微信号|身份证号|学号|私人邮箱)\s*[：:]\s*(\S.{2,})$")
BODY_CONTACT_PATTERNS = (
    re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)"),
    re.compile(r"(?i)(?<![A-Z0-9_.+-])[A-Z0-9][A-Z0-9_.+-]*@[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?)+"),
    re.compile(r"(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?![\d.])"),
)
AVATAR_EXTENSION = {".avif", ".gif", ".jpg", ".jpeg", ".png", ".webp"}
PLACEHOLDERS = {"学员展示名", "作者展示名", "面经标题", "院校名称", "【录取院校】", "【学员展示名】", "填写真实经历的简短摘要。", "用一句话介绍自己的专业方向与准备经历。", "用一句话介绍自己的方向与准备经历。", "用一句话说明这段经历。"}
KINDS = {"院校面经", "申请复盘"}


def scalar(raw: str):
    if not raw or raw in {"null", "~"}:
        return ""
    if raw.startswith('"') and raw.endswith('"'):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'")
    plain = re.split(r"\s+#", raw, maxsplit=1)[0].strip()
    if plain.lower() in {"true", "false"}:
        return plain.lower() == "true"
    return plain


def read_record(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    if text.startswith("{"):
        try:
            data, end = json.JSONDecoder().raw_decode(text)
            if not isinstance(data, dict) or not isinstance(data.get("params", {}), dict):
                return None, None, "JSON 元数据须为对象，params 也须为对象"
            fields = {key: value for key, value in data.items() if key != "params"}
            fields.update({"params." + key: value for key, value in data.get("params", {}).items()})
            return fields, text[end:].lstrip(), None
        except (ValueError, TypeError):
            return None, None, "JSON 元数据无法解析"
    match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)(.*)", text, re.S)
    if not match:
        return None, None, "缺少有效 YAML 或 JSON 元数据"
    fields = {}
    in_params = False
    for line in match.group(1).splitlines():
        found = FIELD.match(line)
        if not found:
            continue
        indent, key, raw = found.groups()
        if not indent:
            in_params = key == "params"
            if key != "params":
                fields[key] = scalar(raw)
        elif in_params and len(indent) == 2:
            fields["params." + key] = scalar(raw)
    return fields, match.group(2), None


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    students: dict[str, Path] = {}
    experiences: list[tuple[Path, dict]] = []
    record_ids: set[str] = set()
    period_ids = set()
    periods_file = root / "data/outcomes.json"
    if periods_file.exists():
        try:
            periods = json.loads(periods_file.read_text(encoding="utf-8-sig"))["periods"]
            period_ids = {str(period["id"]) for period in periods}
        except (KeyError, TypeError, json.JSONDecodeError):
            errors.append("data/outcomes.json: 统计分组数据无法解析")

    def fail(path: Path, message: str):
        errors.append(f"{path.relative_to(root).as_posix()}: {message}")

    for section in ("students", "experiences", "outcomes"):
        for path in sorted((root / "content" / section).rglob("*.md")):
            if path.name == "_index.md":
                continue
            fields, body, error = read_record(path)
            if error:
                fail(path, error)
                continue
            # Drafts are still public in Git: private fields must be checked too.
            for key, value in fields.items():
                if key.rsplit(".", 1)[-1].replace("_", "").lower() in PRIVATE_FIELDS and value:
                    fail(path, "含不应提交的个人联系、身份或密钥字段，请私下核对并移除")
            if PRIVATE_LABEL.search(body) or any(pattern.search(body) for pattern in BODY_CONTACT_PATTERNS):
                fail(path, "正文含明显联系信息、IP 或证件字段，请私下核对并移除")
            avatar = fields.get("params.avatar", "")
            if avatar:
                if not isinstance(avatar, str) or re.search(r"^[a-z][a-z0-9+.-]*:|^//|[\\%?#]|(?:^|/)\.\.(?:/|$)", avatar, re.I) or Path(avatar).suffix.lower() not in AVATAR_EXTENSION:
                    fail(path, "avatar 只允许本页或 static 中的本地图片路径，不允许远程地址或越级路径")
                elif not ((not avatar.startswith("/") and (path.parent / avatar).is_file()) or (root / "static" / avatar.lstrip("/")).is_file()):
                    fail(path, "avatar 对应的本地图片不存在")
            if fields.get("draft") is True:
                continue
            if fields.get("params.status") != "published":
                fail(path, "非草稿学员/经验内容必须明确使用 params.status: published")
            if not fields.get("title") or not fields.get("description"):
                fail(path, "缺少标题或摘要")
            if any(isinstance(value, str) and value in PLACEHOLDERS for value in fields.values()) or re.search(r"^##\s+填写提示|^>\s*米醋保研指南\s*·\s*(?:PR 投稿|学员档案)模板", body, re.M):
                fail(path, "正式内容仍含模板占位或填写提示")
            if not body.strip():
                fail(path, "正式文章正文为空")
            year = fields.get("params.applicationYear", "")
            if year and not re.fullmatch(r"\d{4}", str(year)):
                fail(path, "applicationYear 须为明确的四位公历年份或留空")
            if section == "students":
                if fields.get("type") != "student":
                    fail(path, "学员档案须使用 type: student")
                student_id = fields.get("params.studentId", "")
                if not isinstance(student_id, str) or not ID.fullmatch(student_id):
                    fail(path, "studentId 必须为非空英文小写、数字和连字符标识")
                elif student_id in students:
                    fail(path, "studentId 与已有档案重复")
                else:
                    students[student_id] = path
                if not fields.get("params.displayName"):
                    fail(path, "缺少已同意公开的 displayName")
                for flag in ("featured", "countInOutcomes"):
                    if not isinstance(fields.get("params." + flag, False), bool):
                        fail(path, f"{flag} 须为 true / false，不加引号")
                if fields.get("params.countInOutcomes") is True:
                    if str(fields.get("params.periodId", "")) not in period_ids:
                        fail(path, "计入成果的档案须指定有效 periodId，由维护者核对统计归属")
                    # Unknown undergraduate/destination tiers are valid and must
                    # remain a separate unknown bucket in aggregate rendering.
            else:
                if section == "outcomes":
                    if fields.get("type") != "reflection" or fields.get("params.kind") != "上岸感言":
                        fail(path, "成果栏目的感言须使用 type: reflection 和 kind: 上岸感言")
                    if str(fields.get("params.periodId", "")) not in period_ids:
                        fail(path, "感言须关联有效 periodId，以便在对应届别的整体成果中展示")
                else:
                    if fields.get("type") != "experience":
                        fail(path, "经验文章须使用 type: experience")
                    if fields.get("params.kind") not in KINDS:
                        fail(path, "经验栏目仅收录院校面经与申请复盘；上岸感言请放入成果栏目")
                record_id = fields.get("params.recordId", "")
                if not isinstance(record_id, str) or not ID.fullmatch(record_id):
                    fail(path, "recordId 必须为非空英文小写、数字和连字符标识")
                elif record_id in record_ids:
                    fail(path, "recordId 与已有经验文章重复")
                else:
                    record_ids.add(record_id)
                experiences.append((path, fields))
    for path, fields in experiences:
        student_id = fields.get("params.studentId", "")
        if student_id and student_id not in students:
            fail(path, "studentId 未指向已公开的学员档案；未知作者应留空")
    return errors


def check_tracked_private_files(root: Path) -> list[str]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True)
    if result.returncode:
        return []
    forbidden = ("参考资料/", ".runtime/", ".test-output/", ".test-workspaces/")
    errors = []
    for path in result.stdout.decode("utf-8").split("\0"):
        if path.startswith(forbidden) or "米醋电子工作室保研面经整理" in path:
            errors.append("版本库含原始资料或内部运行文件，请检查暂存范围；原始资料不得公开")
            break
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate(root) + check_tracked_private_files(root)
    if errors:
        print("投稿检查未通过：")
        for error in errors:
            print("- " + error)
        return 1
    print("投稿检查通过：字段、学员 ID、经验关联、统计分组、模板占位与明显私密字段。真实性和公开授权仍须人工审核。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
