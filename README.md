# slow-proxy

A reverse proxy that adds configurable delay to every request. It also detects S3 URLs in response bodies and rewrites them to route through the proxy, so S3 requests are delayed too.

## Installation

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

Or install in editable/development mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
slow-proxy --target <upstream-url> [options]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--target` | *(required)* | Upstream URL to proxy (e.g. `http://localhost:8080`) |
| `--port` | `9000` | Local port to listen on |
| `--delay` | `500` | Delay in milliseconds before forwarding each request |
| `--bind` | `0.0.0.0` | Address to bind to |

### Examples

Proxy requests to a local server with a 500ms delay (default):

```bash
slow-proxy --target http://localhost:8080
```

Custom port and delay:

```bash
slow-proxy --target http://localhost:8080 --port 3000 --delay 1000
```

You can also run it as a module:

```bash
python -m slow_proxy --target http://localhost:8080
```

## How it works

1. Receives an incoming HTTP request
2. Waits for the configured delay
3. Forwards the request to the upstream target
4. For text/JSON responses, scans the body for S3 URLs and rewrites them to route back through the proxy (so those requests are delayed too)
5. Streams binary responses through without buffering
