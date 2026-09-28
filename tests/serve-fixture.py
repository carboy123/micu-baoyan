"""Serve a generated local fixture with a same-origin-only CSP and no caching."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "font-src 'self'; img-src 'self' data:; connect-src 'self'"
)


class FixtureHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default=".runtime/tests/filter-fixture")
    parser.add_argument("--port", type=int, default=1314)
    args = parser.parse_args()
    directory = Path(args.directory)
    directory = (directory if directory.is_absolute() else PROJECT / directory).resolve()
    if not directory.is_relative_to((PROJECT / ".runtime" / "tests").resolve()):
        raise ValueError("Only generated fixtures beneath .runtime/tests/ can be served")
    if not (directory / ".micu-browser-fixture.json").is_file():
        raise ValueError("Generate the browser fixture before starting this server")
    handler = partial(FixtureHandler, directory=str(directory))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"Fixture ready: http://127.0.0.1:{args.port}/experiences/", flush=True)
        print("Same-origin CSP enabled; Cache-Control: no-store", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
