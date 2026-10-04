"""Public fixtures for the Markdown school-book importer; no private sources needed."""
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("school_import", ROOT / "scripts/import-school-interviews.py")
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


def legacy(index):
    year = 2025 if index <= 9 else 2026
    note = "> 整理备注：与 Q2026-024 跨来源疑似重复，保留两份不同回答。\n\n" if index == 18 else ""
    return (f'<a id="m{index:03d}"></a>\n\n### M{index:03d} · 测试学院\n\n'
            + note + f'- **申请年份**：{year} 年保研（用户确认口径）。\n'
            + f'- **原稿年份标注**：{year}届。\n'
            + '- **来源**：[内部原稿](<../../private.md>)，第 1–2 行。\n'
            + '- **原院校标题**：测试院校。\n\n#### 原稿正文\n\n'
            + f'- **基本信息**：{year}届 · 预推免；本科院校层次：211；结果：获得候补资格\n'
            + '- **专业课问题**：闭环控制与开环控制有什么区别？\n\n')


def survey(index):
    school = str(index) if index in (1, 2) else ("山东大学 苏州大学 长安大学" if index == 11 else "测试院校")
    department = str(index) if index in (1, 2) else "测试学院/电子信息"
    return (f'<a id="q2026-{index:03d}"></a>\n\n### Q2026-{index:03d} · {department}\n\n'
            + '- **申请年份**：2026 年保研（用户确认口径）。\n'
            + '- **来源**：[内部问卷](<../../private.xlsx>)，Sheet1 第 4 行，原序号 3。\n'
            + '- **问卷提交日期**：2026/9/25（不代替面试日期）。\n\n'
            + f'**1、面试院校名称**\n\n{school}\n\n'
            + f'**2、学院 / 专业 / 方向**\n\n{department}\n\n'
            + '**3、参加批次**\n\n预推免\n\n'
            + '**4、你的本科院校层次**\n\n211\n\n'
            + '**5、这次申请的最终结果**\n\n未通过\n\n'
            + '**22、具体项目追问**\n\n无\n\n'
            + '**27、给后来者的建议**\n\n保留第一行<br>\n保留第二行 RT\\_DETR。\n\n'
            + '未填写的题号：6、10。\n\n问卷标记为“跳过”的题号：12、13。\n\n')


class SchoolBookImportTests(unittest.TestCase):
    def setUp(self):
        self.base = (ROOT / ".runtime/test-school-interviews").resolve()
        self.base.mkdir(parents=True, exist_ok=True)
        self.temp = Path(tempfile.mkdtemp(prefix="fixture-", dir=self.base)).resolve()
        self.source = self.temp / "按院校整理"
        self.project = self.temp / "project"
        (self.source / "院校").mkdir(parents=True)
        self.project.mkdir()
        self.main = self.source / "院校/测试院校.md"
        self.main.write_text(''.join(legacy(i) for i in range(1, 52)) + ''.join(survey(i) for i in range(3, 114) if i != 11), encoding="utf-8")
        (self.source / "多校合填记录.md").write_text(survey(11), encoding="utf-8")
        (self.source / "待核实条目.md").write_text(survey(1) + survey(2), encoding="utf-8")
        for name in ("README.md", "整理核对记录.md"):
            (self.source / name).write_text("公开人工测试资料；不包含真实学员信息。\n", encoding="utf-8")

    def tearDown(self):
        # 仅删除本测试刚创建且位于项目忽略目录下的确定路径。
        target = self.temp.resolve()
        self.assertTrue(target.is_relative_to(self.base))
        shutil.rmtree(target)

    def test_complete_book_preserves_records_answers_and_multischool_scope(self):
        generated, audit = IMPORTER.build_records(self.source, self.project)
        self.assertEqual(audit["summary"]["publishedRecords"], 162)
        self.assertEqual(audit["summary"]["heldRecords"], 2)
        self.assertEqual(audit["summary"]["publishedByApplicationYear"], {2025: 9, 2026: 153})
        self.assertNotIn(IMPORTER.record_path("Q2026-001", self.project), generated)
        multi, _ = json.JSONDecoder().raw_decode(generated[IMPORTER.record_path("Q2026-011", self.project)])
        self.assertEqual(multi["params"]["recordId"], "survey-2026-011")
        self.assertEqual(multi["params"]["school"], "多校记录")
        self.assertEqual(multi["params"]["schools"], ["山东大学", "苏州大学", "长安大学"])
        q_text = generated[IMPORTER.record_path("Q2026-003", self.project)]
        self.assertIn("**22、具体项目追问**\n\n无", q_text)
        self.assertIn("保留第一行\\\n保留第二行 RT\\_DETR。", q_text)
        parsed, _ = IMPORTER.parse_sources(self.source)
        survey_record = next(record for record in parsed if record["sourceId"] == "Q2026-003")
        self.assertEqual(survey_record["missingNotes"], ["未填写的题号：6、10。", "问卷标记为“跳过”的题号：12、13。"])
        m_text = generated[IMPORTER.record_path("M018", self.project)]
        self.assertIn('{{< relref "/experiences/archive/survey-2026/survey-2026-024.md" >}}', m_text)
        for output in generated.values():
            self.assertNotRegex(output, r"private\.xlsx|private\.md|Sheet1|原序号|用户确认|问卷提交日期")
            self.assertNotRegex(output, r"本条记录的缺项|未填写的题号|问卷标记为|空白或跳过只表示|以上为投稿者对当时经历的回忆")
            self.assertIn("{{< studio-credit >}}", output)

    def test_duplicate_source_identifier_is_rejected(self):
        self.main.write_text(self.main.read_text("utf-8") + legacy(1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "源条目重复"):
            IMPORTER.build_records(self.source, self.project)

    def test_missing_record_is_rejected(self):
        self.main.write_text(self.main.read_text("utf-8").replace(legacy(51), ""), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "源条目集合变化"):
            IMPORTER.build_records(self.source, self.project)

    def test_private_question_range_is_rejected(self):
        value = self.main.read_text("utf-8").replace(survey(3), survey(3) + "**28、私人联系信息**\n\n不可公开\n\n")
        self.main.write_text(value, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "超出范围"):
            IMPORTER.build_records(self.source, self.project)

    def test_existing_stable_id_mismatch_is_rejected(self):
        path = IMPORTER.record_path("M001", self.project)
        path.parent.mkdir(parents=True)
        path.write_text('{"params":{"recordId":"another-record"}}\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "recordId 不一致"):
            IMPORTER.build_records(self.source, self.project)

    def test_repeated_import_is_identical_and_does_not_mutate_sources(self):
        snapshots = {path: path.read_bytes() for path in self.source.rglob("*.md")}
        first, _ = IMPORTER.build_records(self.source, self.project)
        for path, output in first.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(output, encoding="utf-8")
        second, _ = IMPORTER.build_records(self.source, self.project)
        self.assertEqual(first, second)
        self.assertEqual(snapshots, {path: path.read_bytes() for path in snapshots})

    def test_whitespace_and_private_value_handling(self):
        audit = []
        actual = IMPORTER.clean_markdown("第一行  \n第二行\n \n\t\n联系：13800000000\n末尾", "M001", audit)
        self.assertIn("第一行  \n第二行", actual)
        self.assertNotRegex(actual, r"(?m)^[^\S\r\n]+$")
        self.assertNotIn("13800000000", actual)
        self.assertEqual(len(audit), 1)
        self.assertNotIn("13800000000", json.dumps(audit))

    def test_cli_write_requires_explicit_replacement_before_any_changes(self):
        existing = IMPORTER.record_path("M001", self.project)
        existing.parent.mkdir(parents=True)
        original = '{"params":{"recordId":"legacy-001"}}\n\n人工补充内容，不能静默覆盖。\n'
        existing.write_text(original, encoding="utf-8")
        argv = ["import-school-interviews.py", "--source-dir", str(self.source), "--write"]
        with patch.object(IMPORTER, "ROOT", self.project), patch("sys.argv", argv):
            with self.assertRaisesRegex(SystemExit, "1 篇已有面经"):
                IMPORTER.main()
        self.assertEqual(existing.read_text("utf-8"), original)
        self.assertFalse(IMPORTER.record_path("Q2026-003", self.project).exists())
        self.assertFalse((self.project / ".runtime/import-audit/school-interviews.json").exists())
        with patch.object(IMPORTER, "ROOT", self.project), patch("sys.argv", argv + ["--replace-existing"]), contextlib.redirect_stdout(io.StringIO()):
            IMPORTER.main()
        self.assertNotIn("人工补充内容", existing.read_text("utf-8"))
        self.assertTrue(IMPORTER.record_path("Q2026-003", self.project).exists())


if __name__ == "__main__":
    unittest.main()
