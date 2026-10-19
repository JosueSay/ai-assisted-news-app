"""Explicit online check of versioned image fixtures. No DB access or writes."""

from dataclasses import dataclass, field
from time import sleep as time_sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .demo_news import get_demo_news_documents

TIMEOUT_SECONDS = 8
MAX_REDIRECTS = 3
BATCH_PAUSE_SECONDS = 2
ALLOWED_HOSTS = {"upload.wikimedia.org", "thumb.wikimedia.org"}


def validate_image_url(url: str) -> None:
    """Restrict this demo-only checker to the reviewed public image hosts."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.query or parsed.fragment
        or not parsed.path.startswith("/wikipedia/commons/")
        or any(char.isspace() for char in url)
    ):
        raise ValueError("Image URL must be approved public Wikimedia HTTPS without credentials/query")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Validate each Location before issuing another request ourselves.
        return None


@dataclass
class ImageProbe:
    ok: bool = False
    status: int | None = None
    content_type: str = ""
    error: str = ""


def probe_image(url: str, *, open_url=None, sleep=time_sleep) -> ImageProbe:
    """HEAD, with a streaming Range GET fallback for unsupported HEAD.

    A 405/416/501 HEAD response falls back to a ranged GET. Never reads the
    body, even if a server ignores Range. A 429 gets at most one retry, only
    with a numeric Retry-After between 1 and 10 seconds.
    """
    open_url = open_url or build_opener(_NoRedirect()).open
    method = "HEAD"
    redirects = 0
    retried = False
    try:
        while True:
            validate_image_url(url)
            headers = {"User-Agent": "AI-Assisted-News-Demo-ImageCheck/1.0"}
            if method == "GET":
                headers["Range"] = "bytes=0-0"
            request = Request(url, method=method, headers=headers)
            try:
                response = open_url(request, timeout=TIMEOUT_SECONDS)
            except HTTPError as error:
                response = error
            with response:
                status = response.status
                mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                retry_after = response.headers.get("Retry-After", "")
                if (status == 429 and not retried and retry_after.isdecimal()
                        and 1 <= int(retry_after) <= 10):
                    response.close()
                    sleep(int(retry_after))
                    retried = True
                    continue
                if status in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location or redirects >= MAX_REDIRECTS:
                        return ImageProbe(error="Missing Location or redirect limit exceeded", status=status)
                    url = urljoin(url, location)
                    redirects += 1
                    continue
                if status in (405, 416, 501) and method == "HEAD":
                    # Some CDN edges answer HEAD with 416; a ranged GET still
                    # proves accessibility without downloading the file.
                    method = "GET"
                    continue
                if not 200 <= status < 300:
                    return ImageProbe(status=status, content_type=mime, error=f"HTTP {status}")
                if not mime.startswith("image/") or mime == "image/":
                    return ImageProbe(status=status, content_type=mime, error="Missing/non-image Content-Type")
                return ImageProbe(ok=True, status=status, content_type=mime)
    except (URLError, OSError, ValueError):
        # Do not print raw exception text (may contain an untrusted redirect URL).
        return ImageProbe(error="Network/timeout error or rejected image URL")


@dataclass
class ImagesCheckResult:
    visible: int = 0
    checked: int = 0
    failures: list[str] = field(default_factory=list)
    successes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures

    def format(self) -> str:
        return "\n".join([
            f"HTTP image check: {'OK' if self.ok else 'FAILED'}",
            f"Visible fixtures: {self.visible}; unique URLs checked: {self.checked}",
            *self.successes, *self.failures,
            "Versioned fixtures only; no DB accessed or modified.",
        ])


def check_images(documents: list[dict], *, open_url=None, pause=None) -> ImagesCheckResult:
    result = ImagesCheckResult()
    urls: dict[str, list[str]] = {}
    for document in documents:
        image = document["image"]
        slug = document["slug"]
        url = image.get("url")
        if image["type"] == "none":
            if url is not None:
                result.failures.append(f"FAIL {slug}: none requires null URL")
            continue
        result.visible += 1
        if not url:
            result.failures.append(f"FAIL {slug}: visible image requires URL")
            continue
        try:
            validate_image_url(url)
        except ValueError:
            result.failures.append(f"FAIL {slug}: rejected image URL (value omitted)")
            continue
        urls.setdefault(url, []).append(slug)
    for url, slugs in urls.items():
        if result.checked and pause is not None:
            pause(BATCH_PAUSE_SECONDS)
        probe = probe_image(url, open_url=open_url)
        result.checked += 1
        if probe.ok:
            result.successes.append(f"OK {probe.status} {probe.content_type} {url}")
        else:
            result.failures.append(f"FAIL {', '.join(slugs)}: {url} — {probe.error}")
    return result


def main() -> None:
    result = check_images(get_demo_news_documents(), pause=time_sleep)
    print(result.format())
    if not result.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
