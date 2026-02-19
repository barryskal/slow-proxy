import argparse
import asyncio
import logging

from slow_proxy.server import run_server


def main():
    parser = argparse.ArgumentParser(
        prog="slow-proxy",
        description="Reverse proxy that adds configurable delay to every request",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Upstream target URL (e.g. http://localhost:8080)",
    )
    parser.add_argument("--port", type=int, default=9000, help="Local port to listen on (default: 9000)")
    parser.add_argument("--delay", type=int, default=500, help="Delay in milliseconds before forwarding each request (default: 500)")
    parser.add_argument("--bind", default="0.0.0.0", help="Address to bind to (default: 0.0.0.0)")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    target = args.target.rstrip("/")
    logging.getLogger("slow_proxy").info("forwarding to %s with %dms delay on :%d", target, args.delay, args.port)

    asyncio.run(run_server(target=target, port=args.port, delay_ms=args.delay, bind=args.bind))
