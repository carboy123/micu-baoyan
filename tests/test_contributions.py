"""Regression checks for public records; all fixtures live in temp directories."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("contributions", Path(__file__).resolve().parents[1] / "scripts/check-contributions.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class ContributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        (self.root / "data/outcomes.json").write_text(json.dumps({"periods": [{"id": "test-period"}]}), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def record(self, section, name, params="", draft=False, body="这一段记录个人经历。"):
        is_student = section == "students"
        base = '  studentId: test-student\n  displayName: 匿名同学\n' if is_student else f'  kind: 院校面经\n  recordId: test-{name}\n'
        path = self.root / "content" / section / name / "index.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'---\ntitle: 测试经历\ndescription: 独立测试摘要。\ntype: {"student" if is_student else "experience"}\ndraft: {str(draft).lower()}\nparams:\n  status: published\n{base}{params}---\n\n{body}\n', encoding="utf-8")
        return path

    def test_anonymous_experience_does_not_require_student(self):
        self.record("experiences", "anonymous")
        self.assertEqual(checks.validate(self.root), [])

    def test_linked_experience_and_unknown_year_tiers_are_valid(self):
        self.record("students", "one", '  countInOutcomes: true\n  periodId: test-period\n  applicationYear: ""\n')
        self.record("experiences", "one", '  studentId: test-student\n')
        self.assertEqual(checks.validate(self.root), [])

    def test_broken_link_is_rejected(self):
        self.record("experiences", "one", '  studentId: nonexistent\n')
        self.assertTrue(any("未指向" in error for error in checks.validate(self.root)))

    def test_duplicate_student_is_rejected(self):
        self.record("students", "one")
        self.record("students", "two")
        self.assertTrue(any("重复" in error for error in checks.validate(self.root)))

    def test_counted_student_requires_known_period(self):
        self.record("students", "one", '  countInOutcomes: true\n  periodId: unknown\n')
        self.assertTrue(any("periodId" in error for error in checks.validate(self.root)))

    def test_uncounted_student_may_have_no_period(self):
        self.record("students", "one", '  countInOutcomes: false\n')
        self.assertEqual(checks.validate(self.root), [])

    def test_draft_does_not_hide_private_information(self):
        self.record("students", "one", '  phone: SECRET-PHONE-FIXTURE\n', draft=True)
        errors = checks.validate(self.root)
        self.assertTrue(errors)
        self.assertNotIn("SECRET-PHONE-FIXTURE", "\n".join(errors))

    def test_draft_template_allowed_but_published_template_rejected(self):
        path = self.record("students", "one", body="## 填写提示\n正文说明", draft=True)
        self.assertEqual(checks.validate(self.root), [])
        path.write_text(path.read_text(encoding="utf-8").replace("draft: true", "draft: false"), encoding="utf-8")
        self.assertTrue(any("模板占位" in error for error in checks.validate(self.root)))

    def test_year_is_not_inferred_from_cohort(self):
        self.record("students", "one", '  cohort: 2027届\n  applicationYear: ""\n')
        self.assertEqual(checks.validate(self.root), [])

    def test_quoted_boolean_is_rejected(self):
        self.record("students", "one", '  featured: "false"\n')
        self.assertTrue(any("featured" in error for error in checks.validate(self.root)))

    def test_native_json_import_matches_yaml_record(self):
        path = self.record("students", "one")
        data = {"title": "导入学员", "description": "问卷摘要。", "type": "student", "draft": False, "params": {"status": "published", "studentId": "import-one", "displayName": "匿名01", "featured": False, "countInOutcomes": True, "periodId": "test-period", "undergraduateTier": "", "destinationTier": ""}}
        path.write_text(json.dumps(data, ensure_ascii=False) + "\n\n## 个人感言\n\n这一段保留原文。", encoding="utf-8")
        self.assertEqual(checks.validate(self.root), [])

    def test_boolean_inline_comment_is_supported(self):
        self.record("students", "one", '  countInOutcomes: false # maintainer verifies new samples\n')
        self.assertEqual(checks.validate(self.root), [])

    def test_common_private_keys_are_rejected_without_echoing_values(self):
        for key in ("email", "contact", "ip", "userId", "phoneNumber", "phone_number", "IP_address"):
            with self.subTest(key=key):
                self.record("students", "one", f'  {key}: PRIVATE-FIXTURE-VALUE\n', draft=True)
                errors = checks.validate(self.root)
                self.assertTrue(any("个人联系" in error for error in errors))
                self.assertNotIn("PRIVATE-FIXTURE-VALUE", "\n".join(errors))

    def test_obvious_body_contact_patterns_are_rejected_without_echo(self):
        for value in ("13900000000", "+86 13900000000", "test-person@example.invalid", "192.0.2.7"):
            with self.subTest(value=value):
                self.record("students", "one", body=f"需要检查这一段中的 {value} 内容。", draft=True)
                errors = checks.validate(self.root)
                self.assertTrue(any("明显联系信息" in error for error in errors))
                self.assertNotIn(value, "\n".join(errors))

    def test_years_decimal_scores_and_repository_links_are_not_contact_patterns(self):
        self.record("students", "one", body="2027 届，成绩 89.25，版本 1.2.3。项目：https://github.com/example/project 。")
        self.assertEqual(checks.validate(self.root), [])

    def test_experience_record_id_is_required_and_formatted(self):
        for value in ("", "Bad ID", "user/name"):
            with self.subTest(value=value):
                path = self.record("experiences", "one")
                path.write_text(path.read_text(encoding="utf-8").replace("recordId: test-one", f'recordId: "{value}"'), encoding="utf-8")
                self.assertTrue(any("recordId 必须" in error for error in checks.validate(self.root)))

    def test_duplicate_experience_record_id_is_rejected(self):
        self.record("experiences", "one")
        path = self.record("experiences", "two")
        path.write_text(path.read_text(encoding="utf-8").replace("recordId: test-two", "recordId: test-one"), encoding="utf-8")
        self.assertTrue(any("recordId 与已有" in error for error in checks.validate(self.root)))

    def test_avatar_accepts_local_bundle_and_static_assets(self):
        path = self.record("students", "one", '  avatar: portrait.png\n')
        (path.parent / "portrait.png").write_bytes(b"fixture")
        self.assertEqual(checks.validate(self.root), [])
        (self.root / "static/images").mkdir(parents=True)
        (self.root / "static/images/portrait.png").write_bytes(b"fixture")
        for value in ("images/portrait.png", "/images/portrait.png"):
            self.record("students", "one", f'  avatar: {value}\n')
            self.assertEqual(checks.validate(self.root), [])

    def test_avatar_rejects_remote_traversal_and_missing_assets(self):
        for value in ("https://example.invalid/me.png", "//example.invalid/me.png", "../me.png", "data:image/png,test", "/%2Fexample.invalid/me.png", "missing.png"):
            with self.subTest(value=value):
                self.record("students", "one", f'  avatar: "{value}"\n')
                self.assertTrue(any("avatar" in error for error in checks.validate(self.root)))

    def test_actual_hugo_avatar_partial_resolves_prefix_and_blocks_remote(self):
        project = Path(__file__).resolve().parents[1]
        bundled_hugo = project / "tools/hugo/hugo.exe"
        hugo = str(bundled_hugo) if bundled_hugo.is_file() else shutil.which("hugo")
        if not hugo:
            self.skipTest("Hugo is required for the asset rendering regression")
        (self.root / "layouts/_partials/site").mkdir(parents=True)
        shutil.copy2(project / "layouts/_partials/site/student-avatar.html", self.root / "layouts/_partials/site/student-avatar.html")
        (self.root / "hugo.toml").write_text("baseURL='https://example.test/micu-baoyan/'\ndisableKinds=['taxonomy','term','RSS','sitemap']\n", encoding="utf-8")
        (self.root / "layouts/home.html").write_text("fixture", encoding="utf-8")
        (self.root / "layouts/single.html").write_text('avatar={{ partial "site/student-avatar.html" . }}', encoding="utf-8")
        (self.root / "static/images").mkdir(parents=True)
        source_image = project / "static/images/micu-symbol.png"
        shutil.copy2(source_image, self.root / "static/images/portrait.png")
        cases = {
            "bundle": ("portrait.png", "/micu-baoyan/students/bundle/portrait.png"),
            "static-relative": ("images/portrait.png", "/micu-baoyan/images/portrait.png"),
            "static-root": ("/images/portrait.png", "/micu-baoyan/images/portrait.png"),
            "remote": ("https://example.invalid/portrait.png", ""),
            "protocol-relative": ("//example.invalid/portrait.png", ""),
            "traversal": ("../portrait.png", ""),
            "missing": ("missing.png", ""),
        }
        for name, (avatar, _) in cases.items():
            path = self.record("students", name, f'  avatar: "{avatar}"\n')
            if name == "bundle":
                shutil.copy2(source_image, path.parent / "portrait.png")
        result = subprocess.run([hugo, "--source", str(self.root), "--destination", str(self.root / "output")], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name, (_, expected) in cases.items():
            with self.subTest(case=name):
                self.assertEqual((self.root / f"output/students/{name}/index.html").read_text(encoding="utf-8").strip(), "avatar=" + expected)


if __name__ == "__main__":
    unittest.main()
