"""aiohttp application setup and client session lifecycle."""

import asyncio
import socket

import aiohttp
from aiohttp import web

from slow_proxy.proxy import proxy_handler


async def _on_startup(app: web.Application):
    app["client_session"] = aiohttp.ClientSession(auto_decompress=False)


async def _on_cleanup(app: web.Application):
    await app["client_session"].close()


def create_app(target: str, port: int, delay_ms: int) -> web.Application:
    app = web.Application(client_max_size=0)
    app["target"] = target
    app["port"] = port
    app["delay_ms"] = delay_ms

    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)

    # Catch-all route
    app.router.add_route("*", "/{path_info:.*}", proxy_handler)

    return app


async def run_server(target: str, port: int, delay_ms: int, bind: str):
    app = create_app(target, port, delay_ms)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, bind, port)
    await site.start()

    print(f"slow-proxy listening on {bind}:{port}")
    if bind == "0.0.0.0":
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            print(f"  Network: http://{local_ip}:{port}")
        except OSError:
            pass

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
