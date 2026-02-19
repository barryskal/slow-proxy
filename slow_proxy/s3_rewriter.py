"""S3 URL detection, rewriting, and reverse extraction."""

import re

# Matches S3 URLs like:
#   https://bucket.s3.amazonaws.com/key
#   https://bucket.s3.us-east-1.amazonaws.com/key
#   https://s3.amazonaws.com/bucket/key
#   https://s3.us-west-2.amazonaws.com/bucket/key
_S3_URL_RE = re.compile(
    r"https://"
    r"((?:[a-zA-Z0-9._-]+\.)?s3(?:\.[a-zA-Z0-9-]+)?\.amazonaws\.com)"
    r"(/[^\s\"'<>]*)"
)

S3_PATH_PREFIX = "/__s3__/"


def rewrite_s3_urls(body: str, proxy_origin: str) -> str:
    """Replace S3 URLs in body text with proxy-routed equivalents.

    proxy_origin is like ``http://localhost:9000``.
    """

    def _replace(m: re.Match) -> str:
        host = m.group(1)
        path = m.group(2)
        return f"{proxy_origin}{S3_PATH_PREFIX}{host}{path}"

    return _S3_URL_RE.sub(_replace, body)


def extract_s3_url(path: str) -> str | None:
    """If *path* starts with the S3 prefix, reconstruct the original https URL.

    Returns ``None`` when the path is not an S3 proxy path.
    """
    if not path.startswith(S3_PATH_PREFIX):
        return None
    rest = path[len(S3_PATH_PREFIX) :]
    # rest is "host/original/path..."
    return f"https://{rest}"
