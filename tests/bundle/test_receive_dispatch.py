import pytest

from specklepy.api import operations
from specklepy.api.credentials import Account
from specklepy.api.models.current import ServerInfo
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.base import Base
from specklepy.transports.memory import MemoryTransport
from specklepy.transports.server import ServerTransport


class _FakeModel:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True

    def to_base(self):
        base = Base()
        base["received"] = True
        return base


def _transport(project_id: str) -> ServerTransport:
    account = Account(token="t", serverInfo=ServerInfo(url="http://localhost:1"))
    return ServerTransport(project_id, account=account)


def test_bundle_reference_routes_to_receive3(monkeypatch):
    created = []

    def fake_receive3(*args, **kwargs):
        model = _FakeModel(*args, **kwargs)
        created.append(model)
        return model

    monkeypatch.setattr(operations, "receive3", fake_receive3)
    result = operations.receive("bundle.p.m.v", _transport("p"), MemoryTransport())
    assert result["received"] is True
    [model] = created
    assert model.args[1:] == ("p", "m", "v")
    assert model.kwargs == {"mark_received": False}
    assert model.closed


def test_project_mismatch_raises_before_download(monkeypatch):
    monkeypatch.setattr(
        operations, "receive3", lambda *a, **k: pytest.fail("must not download")
    )
    with pytest.raises(SpeckleException, match="belongs to project"):
        operations.receive("bundle.p.m.v", _transport("other"))


def test_requires_a_server_transport(monkeypatch):
    monkeypatch.setattr(
        operations, "receive3", lambda *a, **k: pytest.fail("must not download")
    )
    with pytest.raises(SpeckleException, match="ServerTransport"):
        operations.receive("bundle.p.m.v", MemoryTransport())


def test_malformed_reference_raises():
    with pytest.raises(ValueError):
        operations.receive("bundle.p.m", _transport("p"))


def test_object_hash_takes_the_legacy_path(monkeypatch):
    monkeypatch.setattr(
        operations, "receive3", lambda *a, **k: pytest.fail("must not dispatch")
    )
    local = MemoryTransport()
    obj_id = operations.send(Base(applicationId="x"), [local], use_default_cache=False)
    assert operations.receive(obj_id, local_transport=local).applicationId == "x"
