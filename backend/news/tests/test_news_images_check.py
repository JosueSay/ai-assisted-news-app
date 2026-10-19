"""HTTP boundary is simulated: these tests never use the Internet or MongoDB."""

from copy import deepcopy
from io import BytesIO
from urllib.error import HTTPError, URLError
import urllib.request

import pytest

from news.demo_news import get_demo_news_documents
from news.news_images_check import check_images, main, probe_image, validate_image_url


URL = "https://upload.wikimedia.org/wikipedia/commons/3/37/Garden.jpg"


class Response(BytesIO):
    def __init__(self, status=200, content_type="image/jpeg", **headers):
        super().__init__(b"must not download this body")
        self.status = status
        self.headers = {"Content-Type": content_type, **headers}

    def read(self, *args):
        pytest.fail("Image check must not download the response body")


class Transport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, request, *, timeout):
        assert 0 < timeout <= 10
        self.calls.append(request)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture(autouse=True)
def forbid_network_and_database(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected real network/DB access in offline image tests")
    monkeypatch.setattr(urllib.request.OpenerDirector, "open", forbidden)
    monkeypatch.setattr("news.database.get_news_client", forbidden)
    monkeypatch.setattr("pymongo.MongoClient", forbidden)


@pytest.mark.parametrize("url", [
    "http://upload.wikimedia.org/wikipedia/commons/a.jpg",
    "https:///a.jpg", "https://example.com/demo/img/a.jpg",
    "https://upload.wikimedia.org.evil.test/a.jpg",
    "https://127.0.0.1/a.jpg", "file:///etc/passwd",
    "https://user:password@upload.wikimedia.org/a.jpg",
    URL + "?token=fake", URL + "#fragment",
    "https://upload.wikimedia.org:8443/wikipedia/commons/a.jpg",
])
def test_rejects_unapproved_image_urls_without_network(url):
    with pytest.raises(ValueError):
        validate_image_url(url)


def test_head_checks_status_and_mime_without_downloading_and_closes_response():
    response = Response(content_type="image/jpeg; charset=binary")
    transport = Transport(response)
    result = probe_image(URL, open_url=transport)
    assert result.ok
    assert result.content_type == "image/jpeg"
    assert transport.calls[0].get_method() == "HEAD"
    assert response.closed


@pytest.mark.parametrize("status", [405, 416, 501])
def test_head_unsupported_falls_back_to_partial_get(status):
    error = HTTPError(URL, status, "HEAD unsupported", {}, BytesIO())
    response = Response(206)
    transport = Transport(error, response)
    assert probe_image(URL, open_url=transport).ok
    assert transport.calls[1].get_method() == "GET"
    assert transport.calls[1].get_header("Range") == "bytes=0-0"
    assert error.closed and response.closed


@pytest.mark.parametrize("status", [404, 429, 500])
def test_http_failure_is_not_success(status):
    transport = Transport(HTTPError(URL, status, "failure", {}, BytesIO()))
    result = probe_image(URL, open_url=transport)
    assert not result.ok
    assert str(status) in result.error
    assert len(transport.calls) == 1


def test_rate_limit_respects_short_retry_after_once():
    waits = []
    transport = Transport(
        Response(429, **{"Retry-After": "10"}), Response(),
    )
    assert probe_image(URL, open_url=transport, sleep=waits.append).ok
    assert waits == [10]
    assert len(transport.calls) == 2


@pytest.mark.parametrize("retry_after", ["600", "invalid", "-1"])
def test_rate_limit_with_unbounded_wait_fails(retry_after):
    waits = []
    transport = Transport(Response(429, **{"Retry-After": retry_after}))
    assert not probe_image(URL, open_url=transport, sleep=waits.append).ok
    assert waits == []


def test_persistent_rate_limit_fails_after_one_retry():
    waits = []
    transport = Transport(*(Response(429, **{"Retry-After": "10"}) for _ in range(2)))
    assert not probe_image(URL, open_url=transport, sleep=waits.append).ok
    assert waits == [10]


@pytest.mark.parametrize("mime", ["text/html", "", "application/octet-stream"])
def test_missing_or_non_image_content_type_is_reported(mime):
    result = probe_image(URL, open_url=Transport(Response(content_type=mime)))
    assert not result.ok
    assert "Content-Type" in result.error


@pytest.mark.parametrize("error", [URLError("offline"), TimeoutError()])
def test_network_failure_is_reported(error):
    assert not probe_image(URL, open_url=Transport(error)).ok


def test_redirect_is_followed_only_to_approved_https_host():
    redirect = Response(302, Location=URL)
    transport = Transport(redirect, Response())
    assert probe_image(URL, open_url=transport).ok
    assert len(transport.calls) == 2 and redirect.closed
    unsafe = Transport(Response(302, Location="http://127.0.0.1/private"))
    assert not probe_image(URL, open_url=unsafe).ok
    assert len(unsafe.calls) == 1


def test_redirect_loop_is_bounded():
    transport = Transport(*(Response(302, Location=URL) for _ in range(4)))
    result = probe_image(URL, open_url=transport)
    assert not result.ok
    assert "redirect" in result.error.lower()
    assert len(transport.calls) == 4


def test_checks_each_unique_url_reports_all_affected_slugs_and_preserves_input():
    documents = [
        {"slug": "one", "image": {"type": "photograph", "url": URL}},
        {"slug": "two", "image": {"type": "photograph", "url": URL}},
        {"slug": "none", "image": {"type": "none", "url": None}},
    ]
    before = deepcopy(documents)
    transport = Transport(Response(404))
    report = check_images(documents, open_url=transport)
    assert not report.ok
    assert report.checked == 1 and report.visible == 2
    assert all(value in report.format() for value in ["one", "two", URL, "404"])
    assert len(transport.calls) == 1
    assert documents == before


@pytest.mark.parametrize("image", [
    {"type": "none", "url": URL}, {"type": "photograph", "url": None},
])
def test_incoherent_type_and_url_fail_offline(image):
    assert not check_images([{"slug": "bad", "image": image}]).ok


def test_cli_checks_fixtures_without_database_and_returns_nonzero_on_failure(monkeypatch, capsys):
    transport = Transport(*(Response(404) for _ in get_demo_news_documents()))
    monkeypatch.setattr("news.news_images_check.build_opener", lambda *args: type(
        "Opener", (), {"open": staticmethod(transport)}
    )())
    monkeypatch.setattr("news.news_images_check.time_sleep", lambda seconds: None)
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    assert "FAILED" in capsys.readouterr().out


def test_batch_can_pace_unique_requests_without_sleeping_in_offline_tests():
    waits = []
    docs = [
        {"slug": "one", "image": {"type": "photograph", "url": URL}},
        {"slug": "two", "image": {"type": "photograph", "url": URL.replace("Garden", "Other")}},
    ]
    assert check_images(docs, open_url=Transport(Response(), Response()), pause=waits.append).ok
    assert waits == [2]
