"""Create an isolated browser fixture from a production build, using stdlib only.

All generated files stay under .runtime/tests/. This script never modifies the
source build, content/, data/, or public/, and does not start a server or browser.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import shutil


PROJECT = Path(__file__).resolve().parents[1]
TEST_ROOT = PROJECT / ".runtime" / "tests"
MARKER = ".micu-browser-fixture.json"
DATA_SCRIPT = re.compile(
    r"<script\b[^>]*\bid\s*=\s*(?:\"experience-data\"|'experience-data'|experience-data(?=[\s>]))[^>]*>.*?</script\s*>",
    re.IGNORECASE | re.DOTALL,
)
MAIN = re.compile(r"<main\b[^>]*>.*?</main\s*>", re.IGNORECASE | re.DOTALL)

RECORDS = [
    {
        "id": "fixture-a",
        "title": "【测试数据】甲校电子夏令营面经",
        "description": "合成测试资料：电子项目分析与答辩，不是真实学员经历。",
        "body": "合成测试资料。电子项目分析、嵌入式方案与夏令营答辩。",
        "url": "/experiences/fixture-a/",
        "kind": "院校面经",
        "school": "测试甲大学",
        "college": "测试电子学院",
        "directions": ["电子信息", "嵌入式"],
        "stages": ["夏令营"],
        "applicationYear": 2025,
        "cohort": 2026,
        "author": "测试作者甲",
        "resultStatus": "合成测试资料",
    },
    {
        "id": "fixture-b",
        "title": "【测试数据】甲校电子申请复盘",
        "description": "合成测试资料：电子方向预推免复盘，不是真实学员经历。",
        "body": "合成测试资料。电子方向材料准备与预推免申请复盘。",
        "url": "/experiences/fixture-b/",
        "kind": "申请复盘",
        "school": "测试甲大学",
        "college": "测试电子学院",
        "directions": ["电子信息"],
        "stages": ["预推免"],
        "applicationYear": "2024",
        "cohort": 2025,
        "author": "测试作者乙",
        "resultStatus": "合成测试资料",
    },
    {
        "id": "fixture-c",
        "title": "【测试数据】乙校控制面经（申请年份未知）",
        "description": "合成测试资料：有届别但申请年份为空，不是真实学员经历。",
        "body": "合成测试资料。控制方向夏令营与预推免考核。",
        "url": "/experiences/fixture-c/",
        "kind": "院校面经",
        "school": "测试乙大学",
        "college": "测试控制学院",
        "directions": ["控制"],
        "stages": ["夏令营", "预推免"],
        "applicationYear": "",
        "cohort": 2026,
        "author": "测试作者丙",
        "resultStatus": "合成测试资料",
    },
]


def project_path(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else PROJECT / path).resolve()


def replace_once(pattern: re.Pattern[str], replacement: str, source: str) -> str:
    result, count = pattern.subn(lambda _: replacement, source)
    if count != 1:
        raise ValueError(f"Expected one {pattern.pattern!r} match; found {count}")
    return result


def fixture_notice() -> str:
    return (
        '<div class="notice" role="note"><strong>浏览器测试站 · 合成数据</strong>'
        '<p>本页三条记录仅用于交互验证，不是真实学员经历。'
        '测试文件位于 .runtime/tests，不进入交付内容。</p></div>'
    )


def noindex(source: str) -> str:
    return source.replace(
        "</head>", '<meta name="robots" content="noindex,nofollow"></head>', 1
    )


def detail_html(source: str, record: dict) -> str:
    title = html.escape(record["title"])
    facts = {
        "内容类型": record["kind"],
        "申请院校": record["school"],
        "院系": record["college"],
        "专业方向": " / ".join(record["directions"]),
        "申请阶段": " / ".join(record["stages"]),
        "申请年份": record["applicationYear"] or "未提供",
        "原始届次": record["cohort"],
        "作者展示名": record["author"],
        "结果状态": record["resultStatus"],
    }
    fact_markup = "".join(
        f"<div><dt>{html.escape(key)}</dt><dd>{html.escape(str(value))}</dd></div>"
        for key, value in facts.items()
    )
    back = '<a class="back-link" data-experience-return href="/experiences/">← 返回学员经验</a>'
    main = (
        '<main id="main" tabindex="-1"><div class="experience-detail-wrap">'
        + fixture_notice()
        + back
        + '<article class="article-panel"><header class="article-header">'
        + f'<h1>{title}</h1><p class="article-description">{html.escape(record["description"])}</p>'
        + f'</header><dl class="experience-facts">{fact_markup}</dl>'
        + '<div class="prose"><h2 id="test-instructions">返回筛选验证</h2>'
        + '<p>通过列表筛选后打开本页，再点击顶部或底部返回入口。'
        + '列表 URL、下拉条件、关键词和结果应恢复。刷新详情后再返回也应保留条件。</p>'
        + '<p>可将 return 参数改为外站或非经验列表路径，验证安全回退到本测试站 /experiences/。</p></div>'
        + '<div class="article-end">'
        + back
        + '<button class="text-button" data-print>打印本页</button></div></article></div></main>'
    )
    result = replace_once(MAIN, main, source)
    result = DATA_SCRIPT.sub("", result)
    result = re.sub(r"<title>.*?</title>", lambda _: f"<title>{title} · 浏览器测试站</title>", result, count=1, flags=re.DOTALL)
    return noindex(result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Existing fresh production-build directory")
    parser.add_argument("--output", default=".runtime/tests/filter-fixture", help="Directory beneath .runtime/tests/")
    args = parser.parse_args()
    source = project_path(args.source)
    output = project_path(args.output)
    test_root = TEST_ROOT.resolve()
    if not output.is_relative_to(test_root) or output == test_root:
        raise ValueError("Fixture output must be a subdirectory of .runtime/tests/")
    if source == output or source.is_relative_to(output) or output.is_relative_to(source):
        raise ValueError("Production source and fixture output must not contain each other")
    if output.exists() and any(output.iterdir()) and not (output / MARKER).is_file():
        raise ValueError("Refusing to overwrite a nonempty directory without a fixture marker")
    page = source / "experiences" / "index.html"
    source_html = page.read_text(encoding="utf-8")
    if len(DATA_SCRIPT.findall(source_html)) != 1 or len(MAIN.findall(source_html)) != 1:
        raise ValueError("The production experience page does not match the current DOM contract")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("Production source must not contain symbolic links")
    # Overlay only our own marked fixture, never delete or alter the source build.
    shutil.copytree(source, output, dirs_exist_ok=True)
    payload = json.dumps(RECORDS, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    fixture_html = replace_once(
        DATA_SCRIPT,
        f'<script type="application/json" id="experience-data">{payload}</script>',
        source_html,
    )
    fixture_html = re.sub(
        r"(<main\b[^>]*>)", lambda match: match.group(1) + fixture_notice(), fixture_html, count=1
    )
    (output / "experiences" / "index.html").write_text(noindex(fixture_html), encoding="utf-8")
    for record in RECORDS:
        directory = output / record["url"].strip("/")
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(detail_html(source_html, record), encoding="utf-8")
    manifest = {
        "kind": "micu-browser-fixture",
        "source": str(source),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "recordCount": len(RECORDS),
        "experiencePath": "/experiences/",
        "details": [record["url"] for record in RECORDS],
        "testDataOnly": True,
    }
    (output / MARKER).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created fixture: {output}")
    print(f"Synthetic records: {len(RECORDS)}; source build unchanged")
    print(f'python tests/serve-fixture.py --directory "{output}" --port 1314')
    print("Open http://127.0.0.1:1314/experiences/")


if __name__ == "__main__":
    main()
