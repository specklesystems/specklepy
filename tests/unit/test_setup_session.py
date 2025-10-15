import requests

from specklepy.transports.server.retry_policy import setup_session


def test_session_headers_without_auth():
    """Check that Accept header is set and Authorization is not."""
    session = setup_session(None)
    assert isinstance(session, requests.Session)
    assert session.headers["Accept"] == "text/plain"
    assert "Authorization" not in session.headers


def test_session_headers_with_auth():
    """Check that Authorization header is properly added."""
    token = "abc123"
    session = setup_session(token)
    assert isinstance(session, requests.Session)
    assert session.headers["Authorization"] == f"Bearer {token}"
    assert session.headers["Accept"] == "text/plain"
