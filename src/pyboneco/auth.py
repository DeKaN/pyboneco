import logging
from asyncio import Event
from typing import Callable

from bleak.backends.device import BLEDevice
from bleak.backends.characteristic import BleakGATTCharacteristic
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import ECB

from .enums import BonecoAuthState

logger = logging.getLogger(__name__)


class BonecoAuth:
    _device: BLEDevice
    _nonce = bytearray()
    _device_key = bytearray()

    _state_callback: Callable[["BonecoAuth"], None] | None = None
    _state_changed: Event = Event()
    _current_state: BonecoAuthState = BonecoAuthState.AUTH_ERROR
    _current_auth_level: int = -1
    service_mode_auth_enabled: bool = False
    _keys = {
        0: b"\x00\x00\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02",
        1: b"\x00\x00\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02",
        2: b"\x02\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02",
        3: b"\x03\x03\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02",
        4: b"\x00\x04\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02\x01\x02",
    }

    @property
    def device(self) -> BLEDevice:
        return self._device

    @property
    def address(self) -> str:
        return self._device.address

    @property
    def name(self) -> str:
        return self._device.name

    @property
    def state_changed(self) -> Event:
        return self._state_changed

    @property
    def current_state(self) -> BonecoAuthState:
        return self._current_state

    @property
    def current_auth_level(self) -> int:
        return self._current_auth_level

    def __init__(self, device: BLEDevice, key: str = "") -> None:
        self._device = device
        self._device_key = bytearray.fromhex(key) if key else bytearray()

    def set_auth_state_callback(self, callback: Callable[["BonecoAuth"], None] | None):
        self._state_callback = callback

    def reset_state(self) -> None:
        self._current_state = BonecoAuthState.AUTH_ERROR

    def save(self) -> dict[str, str]:
        return {
            "address": self.address,
            "name": self.name,
            "key": self._device_key.hex(),
        }

    def auth_handler(self, sender: BleakGATTCharacteristic, data: bytearray) -> None:
        logger.debug("[Auth] {0}: {1}".format(sender, data))
        if sender.handle == 0x026:
            if len(data) == 20 and data[0] == 1:
                logger.info("Setting nonce")
                self._nonce = data
                self._set_state(
                    BonecoAuthState.GOT_DEVICE_KEY
                    if self._device_key
                    else BonecoAuthState.GOT_NONCE
                )
            elif data[0] == 4:
                logger.info("Processing auth response")
                if data[2] == 2:
                    self._current_auth_level = data[1]
                    logger.info(f"Changed auth level to {self._current_auth_level}")
                    self._set_state(
                        BonecoAuthState.AUTH_SUCCESS
                        if self._current_auth_level > 0
                        else BonecoAuthState.CONFIRM_WAITING
                    )
                else:
                    self._nonce = bytearray()
                    logger.warning(
                        f"Auth error, current level remains {self._current_auth_level}"
                    )
                    self._set_state(BonecoAuthState.AUTH_ERROR)
            elif data[0:3] == b"\x06\x00\x00":
                logger.info("Saving device key")
                self._device_key = data[3:19]
                self._set_state(BonecoAuthState.GOT_DEVICE_KEY)
        else:
            logger.warning("not supported")

    def characteristics_handler(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        logger.debug("[Chars] {0}: {1}".format(sender, data))
        if sender.handle == 0x029:
            logger.debug(
                f"RSSI level: {int.from_bytes(data[0:1], byteorder='little', signed=True)}, state: {data[1]}"
            )
            if self._current_state < BonecoAuthState.CONFIRMED and data[1] & 1 == 1:
                logger.info("Pairing confirmed")
                self._set_state(BonecoAuthState.CONFIRMED)
        else:
            logger.warning("not supported")

    def generate_request_buffer(self) -> bytes:
        return b"\x05" + bytes(19)

    def get_request_for_auth_level(self, auth_level: int) -> bytes:
        data = self._get_challenge_response(auth_level)
        logger.debug(f'response_hex="{data.hex()}" for auth_level={auth_level}')
        return data

    def _get_challenge_response(self, auth_level: int) -> bytes:
        level = (
            15
            if auth_level == 0 or (auth_level == 1 and self.service_mode_auth_enabled)
            else auth_level
        )
        buffer = self._nonce[2:17] + level.to_bytes(1, byteorder="little")
        data = self._encrypt(buffer, auth_level)
        return b"\x03" + auth_level.to_bytes(1, byteorder="little") + data + b"\x00\x00"

    def _encrypt(self, data: bytes, auth_level: int) -> bytes:
        key = (
            self._device_key
            if auth_level == 1 and not self.service_mode_auth_enabled
            else self._keys[auth_level]
        )
        cipher = Cipher(algorithm=AES(key), mode=ECB(), backend=default_backend())
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()

    def _set_state(self, state: BonecoAuthState) -> None:
        if self._current_state == state:
            logger.debug(f"Skip re-setting state to {state}")
            return
        self._current_state = state
        self._state_changed.set()
        if self._state_callback:
            self._state_callback(self)
