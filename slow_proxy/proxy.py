"""Core proxy handler: delay, forward, rewrite."""

import asyncio
import logging
import zlib

from aiohttp import web

logger = logging.getLogger("slow_proxy")

from slow_proxy.headers import filter_headers, is_scannable
from slow_proxy.s3_rewriter import extract_s3_url, rewrite_s3_urls


async def proxy_handler(request: web.Request) -> web.StreamResponse:
    """Handle every incoming request: delay then forward upstream."""
    target: str = request.app["target"]
    delay_ms: int = request.app["delay_ms"]
    port: int = request.app["port"]
    session = request.app["client_session"]

    # Determine upstream URL
    s3_url = extract_s3_url(request.path_qs)
    if s3_url:
        upstream_url = s3_url
    else:
        upstream_url = target + request.path_qs

    tag = "s3" if s3_url else "proxy"
    logger.info("[%s] %s %s -> %s", tag, request.method, request.path_qs, upstream_url)

    # Apply delay
    if delay_ms > 0:
        await asyncio.sleep(delay_ms / 1000.0)

    # Build outbound headers — filter hop-by-hop and override Accept-Encoding
    out_headers = filter_headers(request.headers, extra_remove={"Host", "Accept-Encoding"})
    out_headers["Accept-Encoding"] = "gzip, deflate"

    # Forward request
    body = await request.read()
    async with session.request(
        method=request.method,
        url=upstream_url,
        headers=out_headers,
        data=body if body else None,
        allow_redirects=False,
    ) as upstream_resp:
        content_type = upstream_resp.headers.get("Content-Type")
        resp_headers = filter_headers(upstream_resp.headers, extra_remove={"Content-Length", "Content-Encoding"})

        if is_scannable(content_type):
            # Buffer, decompress if needed, scan and rewrite
            raw = await upstream_resp.read()
            encoding = upstream_resp.headers.get("Content-Encoding", "").lower()
            if encoding == "gzip":
                raw = zlib.decompress(raw, zlib.MAX_WBITS | 16)
            elif encoding == "deflate":
                raw = zlib.decompress(raw)

            text = raw.decode("utf-8", errors="replace")
            proxy_origin = f"{request.scheme}://{request.host}"
            text = rewrite_s3_urls(text, proxy_origin)
            rewritten = text.encode("utf-8")

            resp_headers["Content-Length"] = str(len(rewritten))
            return web.Response(
                status=upstream_resp.status,
                headers=resp_headers,
                body=rewritten,
            )
        else:
            # Stream binary through without buffering
            resp = web.StreamResponse(
                status=upstream_resp.status,
                headers=resp_headers,
            )
            await resp.prepare(request)
            async for chunk in upstream_resp.content.iter_any():
                await resp.write(chunk)
            await resp.write_eof()
            return resp
