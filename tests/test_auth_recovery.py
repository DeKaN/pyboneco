"""Regression tests for independent authorization and failed BLE sessions."""

import asyncio
from types import SimpleNamespace
from typing import ClassVar

import pytest
from pyboneco import BonecoAuth, BonecoAuthState
from pyboneco import client as client_module
from pyboneco.constants import CHARACTERISTIC_AUTH


class FakeBleakClient:
    instances: ClassVar[list["FakeBleakClient"]] = []

    def __init__(self, address_or_ble_device):
        self.is_connected = True
        self.notifications = {}
        self.stopped = []
        self.fail_to_start = False
        self.send_auth_error = False
        self.reject_immediately = False
        type(self).instances.append(self)

    async def start_notify(self, characteristic, callback):
        if self.fail_to_start:
            raise OSError("notification setup failed")
        self.notifications[characteristic] = callback
        if characteristic == CHARACTERISTIC_AUTH:
            data = (
                bytearray([4, 1, 1])
                if self.reject_immediately
                else bytearray([1] + [0] * 19)
            )
            callback(SimpleNamespace(uuid=CHARACTERISTIC_AUTH), data)

    async def write_gatt_char(self, characteristic, data):
        if self.send_auth_error:
            self.notifications[CHARACTERISTIC_AUTH](
                SimpleNamespace(uuid=CHARACTERISTIC_AUTH),
                bytearray([4, 1, 1]),
            )

    async def stop_notify(self, characteristic):
        self.stopped.append(characteristic)

    async def disconnect(self):
        self.is_connected = False


@pytest.fixture
def fake_client(monkeypatch):
    FakeBleakClient.instances.clear()
    monkeypatch.setattr(client_module, "BleakClient", FakeBleakClient)
    auth = BonecoAuth(SimpleNamespace(name="H700", address="AA:BB"), "00" * 16)
    client = client_module.BonecoClient(auth)
    return auth, client, client._client


def test_auth_events_are_per_device():
    first = BonecoAuth(SimpleNamespace(name="H700", address="AA:BB"))
    second = BonecoAuth(SimpleNamespace(name="H700", address="CC:DD"))
    first._set_state(BonecoAuthState.GOT_NONCE)

    assert first.state_changed.is_set()
    assert not second.state_changed.is_set()
    first.reset_state()
    assert not first.state_changed.is_set()


def test_rejected_authorization_raises_and_stops_notifications(fake_client):
    auth, client, fake = fake_client
    fake.send_auth_error = True

    with pytest.raises(RuntimeError, match="authorization rejected"):
        asyncio.run(client.authorize(timeout=0.1))

    assert CHARACTERISTIC_AUTH in fake.stopped
    assert auth.current_state == BonecoAuthState.AUTH_ERROR


def test_notification_exception_is_not_swallowed(fake_client):
    _, client, fake = fake_client
    fake.fail_to_start = True

    with pytest.raises(OSError, match="notification setup failed"):
        asyncio.run(client.authorize(timeout=0.1))


def test_rejection_before_nonce_wakes_authorization(fake_client):
    _, client, fake = fake_client
    fake.reject_immediately = True

    with pytest.raises(RuntimeError, match="authorization rejected"):
        asyncio.run(client.authorize(timeout=0.1))


def test_incomplete_auth_does_not_read_gatt(fake_client, monkeypatch):
    _, client, _ = fake_client

    async def incomplete_authorize():
        pass

    monkeypatch.setattr(client, "authorize", incomplete_authorize)
    with pytest.raises(RuntimeError, match="authorization failed"):
        asyncio.run(client.get_device_name())


def test_authorization_timeout_stops_notifications(fake_client):
    _, client, fake = fake_client

    with pytest.raises(TimeoutError):
        asyncio.run(client.authorize(timeout=0.01))

    assert CHARACTERISTIC_AUTH in fake.stopped


def test_disconnect_replaces_client(fake_client):
    auth, client, fake = fake_client
    asyncio.run(client.disconnect())

    assert client._client is not fake
    assert auth.current_state == BonecoAuthState.AUTH_ERROR


@pytest.mark.parametrize("payload", [b"", b"\x04", b"\x04\x01", b"\x06\x00\x00"])
def test_malformed_auth_packet_wakes_waiter_with_error(payload):
    auth = BonecoAuth(SimpleNamespace(name="H700", address="AA:BB"))
    auth.auth_handler(SimpleNamespace(uuid=CHARACTERISTIC_AUTH), bytearray(payload))
    assert auth.current_state == BonecoAuthState.AUTH_ERROR
    assert auth.state_changed.is_set()


def test_persistent_client_does_not_create_unsubscribed_connection(fake_client):
    _, client, fake = fake_client
    client.persistent_session = True
    fake.is_connected = False
    with pytest.raises(RuntimeError, match="connection was lost"):
        asyncio.run(client.get_state())


@pytest.mark.parametrize("advertised_name", [None, "Renamed H700"])
def test_protocol_model_can_override_advertised_name(advertised_name):
    auth = BonecoAuth(SimpleNamespace(name=advertised_name, address="AA:BB"))
    auth.model_name = "H700"
    assert auth.name == "H700"
