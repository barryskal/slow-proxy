# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

slow-proxy is a reverse proxy that adds configurable delay to every request. It detects S3 URLs in response bodies and rewrites them to route back through the proxy so S3 requests are also delayed. Built with Python 3.10+ and aiohttp.

## Commands

```bash
# Install (editable/dev mode)
pip install -e .

# Run
slow-proxy --target http://localhost:8080 --port 9000 --delay 500
python -m slow_proxy --target http://localhost:8080
```

No test suite exists yet.

## Architecture

The request lifecycle: CLI (`cli.py`) → server setup (`server.py`) → catch-all route → `proxy_handler` (`proxy.py`).

- **cli.py** — argparse entry point, registered as `slow-proxy` console script
- **server.py** — creates the aiohttp app, manages `ClientSession` lifecycle, binds the catch-all route
- **proxy.py** — core handler: sleeps for the configured delay, forwards the request upstream, then either buffers text/JSON responses to rewrite S3 URLs or streams binary responses through untouched
- **headers.py** — hop-by-hop header filtering (RFC 2616) and content-type classification for deciding which responses to scan
- **s3_rewriter.py** — regex-based S3 URL detection/rewriting and reverse extraction via the `/__s3__/` path prefix

Key design details:
- The proxy forces `Accept-Encoding: gzip, deflate` upstream and decompresses before scanning, so S3 URL rewriting works regardless of upstream compression
- S3 URLs are rewritten to `http://localhost:{port}/__s3__/{s3_host}/{path}`, and incoming requests matching that prefix are reverse-mapped back to `https://{s3_host}/{path}`
- Binary/non-text responses are streamed chunk-by-chunk without buffering
