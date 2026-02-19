"""Hop-by-hop header filtering and content-type helpers."""

# Headers that must not be forwarded between proxy hops (RFC 2616 Section 13.5.1)
HOP_BY_HOP = frozenset(
    h.lower()
    for h in [
        "Connection",
        "Keep-Alive",
        "Proxy-Authenticate",
        "Proxy-Authorization",
        "TE",
        "Trailers",
        "Transfer-Encoding",
        "Upgrade",
    ]
)

# Content types whose bodies should be scanned for S3 URLs
_SCANNABLE_TYPES = (
    "text/",
    "application/json",
    "application/xml",
    "application/javascript",
)


def filter_headers(headers, *, extra_remove=frozenset()):
    """Return a dict of headers with hop-by-hop and extra keys removed."""
    removed = HOP_BY_HOP | {k.lower() for k in extra_remove}
    return {k: v for k, v in headers.items() if k.lower() not in removed}


def is_scannable(content_type: str | None) -> bool:
    """Check whether the content type indicates a text/JSON body worth scanning."""
    if not content_type:
        return False
    ct = content_type.lower().split(";")[0].strip()
    return any(ct.startswith(prefix) if prefix.endswith("/") else ct == prefix for prefix in _SCANNABLE_TYPES)
