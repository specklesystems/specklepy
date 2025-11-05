import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def setup_session(auth_token: str | None) -> requests.Session:
    """
    Sets up a requests.Session with a basic retry policy
    to retry on all the usual retryable status codes, with a back off policy:
        1st: 0ms,
        2nd: 500ms,
        3rd: 1500ms.

    Also sets "Accept": "text/plain" header (because this is what ServerTransport needs)
    and (if a auth_token is provided) the Authorization header
    """

    session = requests.Session()
    retry_policy = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504, 520, 408, 429),
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_policy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update(
        {
            "Accept": "text/plain",
        }
    )

    if auth_token is not None:
        session.headers.update(
            {
                "Authorization": f"Bearer {auth_token}",
            }
        )

    return session
