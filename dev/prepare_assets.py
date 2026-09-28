"""Optional developer asset setup; normal preview/build never uses the network.

Verified local assets are reused. Adobe assets are pinned to official repository
commits and Git blob identities; GitHub's blob API avoids slow raw CDN transfers.
"""
import base64
import hashlib
from http.client import HTTPException
import io
import json
from pathlib import Path
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "DEPENDENCIES.json"
THEME_URL = "https://codeload.github.com/alex-shpak/hugo-book/zip/refs/tags/v0.15.0"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
# name, repository, pinned commit, repository path, official Git blob SHA-1, size
ASSETS = [
    ("SourceHanSansCN-Regular.otf", "source-han-sans", "a4f7cf94edfb9d7ffbdfc4841de276358bd7e0f2", "SubsetOTF/CN/SourceHanSansCN-Regular.otf", "5e6605995d5cbc432c4273f566a5f2b8c376c682", 8429224),
    ("SourceHanSerifCN-Regular.otf", "source-han-serif", "7889f11bf31170b5d092a083b357c8c8130f89e0", "SubsetOTF/CN/SourceHanSerifCN-Regular.otf", "a4feb5f2461886dbf9cfe575974f0a68940c6bf9", 11626108),
    ("source-han-sans-LICENSE.txt", "source-han-sans", "a4f7cf94edfb9d7ffbdfc4841de276358bd7e0f2", "LICENSE.txt", "3ff0ccaba06857bf292ade9a50f16a0f02b3b8d4", 4463),
    ("source-han-serif-LICENSE.txt", "source-han-serif", "7889f11bf31170b5d092a083b357c8c8130f89e0", "LICENSE.txt", "07235a78b936958799812313565ba0d03e7cd7dd", 4463),
]


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def download(url, attempts=3):
    """Bound each socket wait, total transfer size, duration, and retry count."""
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Micu-Baoyan-Setup/1.0"})
            deadline = time.monotonic() + 180
            chunks, total = [], 0
            with OPENER.open(request, timeout=30) as response:
                while chunk := response.read(256 * 1024):
                    total += len(chunk)
                    if total > 64 * 1024 * 1024 or time.monotonic() > deadline:
                        raise TimeoutError("Asset exceeds bounded size or transfer duration")
                    chunks.append(chunk)
            return b"".join(chunks)
        except (OSError, TimeoutError, HTTPException) as error:
            if attempt == attempts - 1:
                raise
            print(f"Retry {attempt + 1}/{attempts - 1}: {url} ({error})", flush=True)
            time.sleep(attempt + 1)


def tree_sha256(directory):
    digest = hashlib.sha256()
    paths = sorted((p for p in directory.rglob("*") if p.is_file()), key=lambda p: p.relative_to(directory).as_posix())
    for path in paths:
        if path.is_symlink():
            raise ValueError("Theme files must not be symlinks")
        digest.update(path.relative_to(directory).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def prepare_theme(existing):
    target = ROOT / "themes" / "hugo-book"
    if target.is_dir() and any(target.iterdir()):
        if not existing or existing.get("hash_scope") != "extracted-tree":
            raise RuntimeError("Existing theme has no verified tree manifest; preserve it and review before setup.")
        if tree_sha256(target) != existing["sha256"]:
            raise RuntimeError("Theme differs from its verified manifest; local changes were preserved.")
        print("Cached and verified: Hugo Book v0.15.0", flush=True)
        return existing
    data = download(THEME_URL)
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for entry in archive.infolist():
            parts = Path(entry.filename).parts[1:]
            if not parts or entry.is_dir():
                continue
            dest = target.joinpath(*parts).resolve()
            if not dest.is_relative_to(target.resolve()):
                raise ValueError("Unsafe archive path")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(archive.read(entry))
    digest = tree_sha256(target)
    if existing and existing.get("hash_scope") == "extracted-tree" and existing["sha256"] != digest:
        raise ValueError("Downloaded theme does not match the pinned manifest")
    return {"name": "Hugo Book", "version": "v0.15.0", "url": THEME_URL, "path": "themes/hugo-book", "sha256": digest, "hash_scope": "extracted-tree"}


def verify_asset(blob, asset):
    name, _, _, _, expected_git, expected_size = asset
    identity = hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest()
    return len(blob) == expected_size and identity == expected_git and (not name.endswith(".otf") or blob.startswith(b"OTTO"))


def fetch_asset(asset, url):
    _, repo, _, _, git_sha, _ = asset
    api_url = f"https://api.github.com/repos/adobe-fonts/{repo}/git/blobs/{git_sha}"
    try:
        response = json.loads(download(api_url))
        if response.get("encoding") != "base64":
            raise ValueError("Unexpected GitHub blob encoding")
        blob = base64.b64decode(response["content"])
    except (OSError, ValueError, KeyError, HTTPException) as error:
        print(f"Official blob API unavailable; trying pinned raw URL ({error})", flush=True)
        blob = download(url)
    if not verify_asset(blob, asset):
        raise ValueError(f"Official asset identity mismatch: {asset[0]}")
    return blob


def main():
    previous = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else []
    previous_by_name = {item["name"]: item for item in previous}
    theme = prepare_theme(previous_by_name.get("Hugo Book"))
    manifests = [theme]
    font_dir = ROOT / "static" / "fonts"
    cache_dir = ROOT / ".runtime" / "asset-cache"
    font_dir.mkdir(parents=True, exist_ok=True)
    for asset in ASSETS:
        name, repo, commit, source, git_sha, size = asset
        url = f"https://raw.githubusercontent.com/adobe-fonts/{repo}/{commit}/{source}"
        path = font_dir / name
        blob = path.read_bytes() if path.exists() else b""
        if verify_asset(blob, asset):
            print(f"Cached and verified: {name}", flush=True)
        else:
            blob = fetch_asset(asset, url)
            cache_dir.mkdir(parents=True, exist_ok=True)
            temporary = cache_dir / name
            temporary.write_bytes(blob)
            temporary.replace(path)
            print(f"Downloaded and verified: {name} ({len(blob):,} bytes)", flush=True)
        manifests.append({"name": name, "url": url, "path": f"static/fonts/{name}", "source_commit": commit, "git_blob_sha1": git_sha, "sha256": sha256(blob), "size": size})
    managed_names = {item["name"] for item in manifests}
    manifests.extend(item for item in previous if item["name"] not in managed_names)
    rendered = json.dumps(manifests, ensure_ascii=False, indent=2) + "\n"
    if not MANIFEST.exists() or MANIFEST.read_text(encoding="utf-8") != rendered:
        MANIFEST.write_text(rendered, encoding="utf-8")
    print("Local theme and font assets ready.")


if __name__ == "__main__":
    main()
