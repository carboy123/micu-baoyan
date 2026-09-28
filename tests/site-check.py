#!/usr/bin/env python3
"""检查 Hugo 静态产物。仅用标准库，不启动服务，也不改写文件。

用法：python tests/site-check.py public
      python tests/site-check.py .runtime/builds/subpath --prefix /micu-baoyan/
      python tests/site-check.py .runtime/builds/dev --development
      python tests/site-check.py public --skip-original  # 公开克隆或 CI 无原始面经
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


SOURCE_NAME = "2026-8-7 米醋电子工作室保研面经整理 231938.md"
SOURCE_SHA256 = "737E1E09BFA65642F03BB01902597A258517E6A103CBDABC946483178AE7BED0"
CSS_URL = re.compile(r"url\(\s*(?:\"([^\"]*)\"|'([^']*)'|([^)]*?))\s*\)", re.I)
CSS_IMPORT = re.compile(r"@import\s+(?:\"([^\"]*)\"|'([^']*)')", re.I)
AUTO_LINK_RELS = {"stylesheet", "icon", "preload", "modulepreload", "prefetch", "preconnect", "dns-prefetch", "manifest"}


@dataclass
class Reference:
    url: str
    context: str
    automatic: bool = False


@dataclass
class Page:
    path: Path
    ids: set[str] = field(default_factory=set)
    duplicate_ids: set[str] = field(default_factory=set)
    refs: list[Reference] = field(default_factory=list)
    json_blocks: list[tuple[str, str]] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    h1_count: int = 0


class PageParser(HTMLParser):
    def __init__(self, page: Page):
        super().__init__(convert_charrefs=True)
        self.page = page
        self.capture_json: str | None = None
        self.json_parts: list[str] = []
        self.capture_style = False
        self.style_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            if element_id in self.page.ids:
                self.page.duplicate_ids.add(element_id)
            self.page.ids.add(element_id)
        if tag == "a" and values.get("name"):
            self.page.ids.add(values["name"])
        if tag == "h1":
            self.page.h1_count += 1
        if values.get("style"):
            self.page.styles.append(values["style"])
        context = f"{tag}，行 {self.getpos()[0]}"
        if "href" in values and values["href"]:
            rels = set((values.get("rel") or "").lower().split())
            self.page.refs.append(Reference(values["href"], context, tag == "link" and bool(rels & AUTO_LINK_RELS)))
        for attr in ("src", "poster", "data-src"):
            if values.get(attr):
                self.page.refs.append(Reference(values[attr], f"{context}，{attr}", True))
        if tag == "object" and values.get("data"):
            self.page.refs.append(Reference(values["data"], context, True))
        if values.get("action"):
            self.page.refs.append(Reference(values["action"], context))
        if values.get("srcset"):
            # 本站不使用 data URI srcset；单独的 data URI 不依赖远程文件。
            if not values["srcset"].strip().lower().startswith("data:"):
                for candidate in values["srcset"].split(","):
                    parts = candidate.strip().split()
                    if parts:
                        self.page.refs.append(Reference(parts[0], f"{context}，srcset", True))
        if tag == "script" and (values.get("type") or "").lower() in ("application/json", "application/ld+json"):
            self.capture_json = values.get("id") or "anonymous-json"
            self.json_parts = []
        if tag == "style":
            self.capture_style = True
            self.style_parts = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self.capture_json is not None:
            self.json_parts.append(data)
        if self.capture_style:
            self.style_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.capture_json is not None:
            self.page.json_blocks.append((self.capture_json, "".join(self.json_parts)))
            self.capture_json = None
        if tag == "style" and self.capture_style:
            self.page.styles.append("".join(self.style_parts))
            self.capture_style = False


class Checker:
    def __init__(self, build: Path, source: Path, prefix: str, development: bool, skip_original: bool = False):
        self.build = build.resolve()
        self.source = source.resolve()
        self.prefix = "/" + prefix.strip("/") + "/" if prefix.strip("/") else "/"
        self.development = development
        self.skip_original = skip_original
        self.pages: dict[Path, Page] = {}
        self.errors: list[str] = []
        self.checked_refs = 0
        self.checked_json = 0
        self.search_blocks = 0
        self.experience_blocks = 0
        self.forbidden_search_pages = self.read_forbidden_content()

    def label(self, path: Path) -> str:
        try:
            return path.relative_to(self.build).as_posix()
        except ValueError:
            return str(path)

    def fail(self, path: Path | str, message: str) -> None:
        label = self.label(path) if isinstance(path, Path) else path
        self.errors.append(f"{label}: {message}")

    def read_forbidden_content(self) -> set[str]:
        forbidden = set()
        content = self.source / "content"
        for path in content.rglob("*.md"):
            text = path.read_text(encoding="utf-8-sig")
            if not text.startswith("---"):
                continue
            frontmatter = text.split("---", 2)[1]
            status = re.search(r"^  status:\s*['\"]?([^'\"\s]+)", frontmatter, re.M)
            draft = re.search(r"^draft:\s*true\s*$", frontmatter, re.M | re.I)
            if draft or (status and status.group(1) in ("planned", "preview")):
                relative = path.relative_to(content)
                if relative.name == "_index.md":
                    route = relative.parent
                else:
                    route = relative.with_suffix("")
                forbidden.add((route / "index.html").as_posix())
        return forbidden

    def page_url(self, path: Path) -> str:
        relative = path.relative_to(self.build).as_posix()
        if relative.endswith("index.html"):
            relative = relative[:-len("index.html")]
        return self.prefix + relative

    def local_target(self, origin: Path, reference: Reference) -> tuple[Path, str] | None:
        raw = reference.url.strip()
        if not raw:
            return None
        parts = urlsplit(raw)
        if parts.scheme in ("mailto", "tel", "data", "blob"):
            return None
        if parts.scheme == "javascript":
            self.fail(origin, f"不支持的 javascript 链接 {raw!r}（{reference.context}）")
            return None
        if parts.scheme or parts.netloc:
            if parts.hostname not in ("localhost", "127.0.0.1", "::1"):
                if reference.automatic:
                    self.fail(origin, f"自动加载资源依赖远程地址 {raw!r}（{reference.context}）")
                return None
        joined = urlsplit(urljoin(self.page_url(origin), parts.path + ("?" + parts.query if parts.query else "") + ("#" + parts.fragment if parts.fragment else "")))
        decoded_path = unquote(joined.path)
        if not decoded_path.startswith(self.prefix):
            self.fail(origin, f"链接未保留部署前缀 {self.prefix!r}: {raw!r}（{reference.context}）")
            return None
        relative = decoded_path[len(self.prefix):]
        target = (self.build / relative).resolve()
        if not target.is_relative_to(self.build):
            self.fail(origin, f"链接越过产物目录 {raw!r}（{reference.context}）")
            return None
        if target.is_dir() or decoded_path.endswith("/"):
            target = target / "index.html"
        return target, unquote(joined.fragment)

    def check_reference(self, origin: Path, reference: Reference) -> Path | None:
        result = self.local_target(origin, reference)
        if result is None:
            return None
        self.checked_refs += 1
        target, fragment = result
        if not target.is_file():
            self.fail(origin, f"目标不存在: {reference.url!r} → {self.label(target)}（{reference.context}）")
            return target
        if fragment and target.suffix.lower() in (".html", ".htm"):
            page = self.pages.get(target)
            # 文本片段指令不是 HTML id。
            fragment = fragment.split(":~:text=", 1)[0]
            if fragment and (page is None or fragment not in page.ids):
                self.fail(origin, f"锚点不存在: {reference.url!r} → {self.label(target)}#{fragment}（{reference.context}）")
        return target

    def check_css(self, path: Path, css: str) -> None:
        # 移除注释，避免把注释内示例当成自动加载资源。
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        for pattern in (CSS_URL, CSS_IMPORT):
            for match in pattern.finditer(css):
                url = next((group.strip() for group in match.groups() if group is not None), "")
                self.check_reference(path, Reference(url, "CSS url/@import", True))

    def check_data(self, path: Path, name: str, raw: str) -> None:
        self.checked_json += 1
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            self.fail(path, f"JSON {name!r} 无法解析: {exc}")
            return
        if name not in ("search-data", "experience-data"):
            return
        if not isinstance(data, list):
            self.fail(path, f"{name} 必须为数组")
            return
        if name == "search-data":
            self.search_blocks += 1
            if not data:
                self.fail(path, "search-data 为空，示例文章与术语未进入搜索")
        else:
            self.experience_blocks += 1
            if not self.development and data:
                self.fail(path, f"首版生产 experience-data 应为空，实际含 {len(data)} 条")
        ids = set()
        for index, record in enumerate(data):
            if not isinstance(record, dict):
                self.fail(path, f"{name}[{index}] 必须为对象")
                continue
            record_id = record.get("id")
            if record_id and record_id in ids:
                self.fail(path, f"{name} 重复 id: {record_id!r}")
            if record_id:
                ids.add(record_id)
            url = record.get("url")
            if not isinstance(url, str) or not url:
                self.fail(path, f"{name}[{index}] 缺少有效 url")
                continue
            target = self.check_reference(path, Reference(url, f"{name}[{index}]"))
            if name == "search-data":
                if record.get("status") in ("planned", "preview"):
                    self.fail(path, f"search-data 收录了 {record['status']} 记录: {url}")
                if target and target.is_relative_to(self.build):
                    relative = target.relative_to(self.build).as_posix()
                    if relative in self.forbidden_search_pages or relative.startswith("preview/"):
                        self.fail(path, f"search-data 收录了待补充或草稿预览: {url}")

    def check_original(self) -> None:
        candidates = [self.source / SOURCE_NAME, self.source / "参考资料" / SOURCE_NAME]
        original = next((path for path in candidates if path.is_file()), candidates[0])
        if not original.is_file():
            self.fail("原始素材", f"找不到保留的源文件 {SOURCE_NAME}")
            return
        digest = hashlib.sha256()
        with original.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest().upper() != SOURCE_SHA256:
            self.fail("原始素材", "SHA256 与已确认基准不一致；未输出原文")

    def run(self) -> int:
        if not self.build.is_dir():
            self.fail("产物目录", f"不存在: {self.build}")
        for path in sorted(self.build.rglob("*.html")):
            path = path.resolve()
            page = Page(path)
            parser = PageParser(page)
            try:
                parser.feed(path.read_text(encoding="utf-8-sig"))
                parser.close()
            except (UnicodeError, ValueError) as exc:
                self.fail(path, f"HTML 无法解析: {exc}")
            self.pages[path] = page
        if not self.pages:
            self.fail("产物目录", "没有找到 HTML 页面")
        for path, page in self.pages.items():
            if page.h1_count != 1:
                self.fail(path, f"应有且只有一个 h1，实际 {page.h1_count} 个")
            if page.duplicate_ids:
                self.fail(path, f"重复 HTML id: {', '.join(sorted(page.duplicate_ids))}")
            if not self.development and path.relative_to(self.build).parts[0] == "preview":
                self.fail(path, "生产产物包含模板预览页")
            for reference in page.refs:
                self.check_reference(path, reference)
            for css in page.styles:
                self.check_css(path, css)
            for name, raw in page.json_blocks:
                self.check_data(path, name, raw)
        for path in sorted(self.build.rglob("*.css")):
            self.check_css(path, path.read_text(encoding="utf-8-sig"))
        for path in sorted(self.build.rglob("*.json")):
            self.check_data(path, path.stem, path.read_text(encoding="utf-8-sig"))
        if not self.search_blocks:
            self.fail("搜索索引", "未发现 search-data JSON")
        if not self.experience_blocks:
            self.fail("经验索引", "未发现 experience-data JSON")
        if not self.skip_original:
            self.check_original()
        mode = "开发" if self.development else "生产"
        print(f"{mode}产物检查：{len(self.pages)} 个 HTML、{self.checked_refs} 个本地引用、{self.checked_json} 处 JSON；部署前缀 {self.prefix}")
        if self.errors:
            print(f"失败：{len(self.errors)} 项")
            for error in self.errors:
                print(f"  - {error}")
            return 1
        print("通过：内链/锚点、资源、页面标题、索引隔离与离线依赖均符合要求。")
        if self.skip_original:
            print("原始素材哈希：已显式跳过（公开克隆／CI 不包含本地原始素材）。")
        else:
            print("原始素材哈希：通过。")
        return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("build", type=Path, help="Hugo 构建产物目录")
    parser.add_argument("--prefix", default="/", help="部署路径前缀，例如 /micu-baoyan/")
    parser.add_argument("--development", action="store_true", help="允许草稿预览页；仍要求预览不进入搜索")
    parser.add_argument("--skip-original", action="store_true", help="公开克隆或 CI 使用：仅跳过不随仓库发布的原始面经哈希检查")
    args = parser.parse_args()
    return Checker(args.build, Path(__file__).resolve().parents[1], args.prefix, args.development, args.skip_original).run()


if __name__ == "__main__":
    raise SystemExit(main())
