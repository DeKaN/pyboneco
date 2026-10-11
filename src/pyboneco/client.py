import asyncio
import logging

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS, establish_connection

from .advertising_data import BonecoAdvertisingData
from .auth import BonecoAuth, BonecoAuthState
from .constants import (
    CHARACTERISTIC_AUTH,
    CHARACTERISTIC_AUTH_AND_SERVICE,
    CHARACTERISTIC_DEVICE_INFO,
    CHARACTERISTIC_DEVICE_NAME,
    CHARACTERISTIC_DEVICE_STATE,
)
from .device_info import BonecoDeviceInfo
from .device_state import BonecoDeviceState

logger = logging.getLogger(__name__)


class BonecoClient:
    _auth_data: BonecoAuth
    _client: BleakClient

    def __init__(self, auth_data: BonecoAuth, *, persistent_session: bool = False):
        self._client = BleakClient(address_or_ble_device=auth_data.device)
        self._auth_data = auth_data
        self.persistent_session = persistent_session

    def require_auth(func):
        async def wrapped(self, *args, **kwargs):
            await self._ensure_connected()
            if self._auth_data.current_state != BonecoAuthState.AUTH_SUCCESS:
                await self.authorize()
                if self._auth_data.current_state != BonecoAuthState.AUTH_SUCCESS:
                    raise RuntimeError(
                        f"{self._get_internal_name()}: authorization failed"
                    )
            return await func(self, *args, **kwargs)

        return wrapped

    @staticmethod
    async def find_boneco_devices(
        timeout: float = 5.0,
    ) -> dict[BLEDevice, BonecoAdvertisingData]:
        devices_data = await BleakScanner.discover(timeout, return_adv=True)
        manufacturer_data = {
            device: BonecoAdvertisingData(
                *next(iter(adv_data.manufacturer_data.items()))
            )
            for device, adv_data in devices_data.values()
            if len(adv_data.manufacturer_data) > 0
        }
        return {k: v for k, v in manufacturer_data.items() if v.is_boneco_device}

    @property
    def is_connected(self) -> bool:
        return self._client.is_connected

    async def connect(self) -> None:
        if not self.is_connected:
            self._auth_data.reset_state()
            self._client = await establish_connection(
                BleakClient,
                self._auth_data.device,
                self._auth_data.name,
                max_attempts=5,
            )

    async def disconnect(self) -> None:
        try:
            await self._client.disconnect()
        except BLEAK_RETRY_EXCEPTIONS as ex:
            logger.warning(f"{self._get_internal_name()}: Error disconnecting: {ex}")
        else:
            logger.debug(
                f"{self._get_internal_name()}: Disconnect completed successfully"
            )
        finally:
            self._auth_data.reset_state()
            # A failed disconnect must not leave a client that appears connected.
            self._client = BleakClient(address_or_ble_device=self._auth_data.device)

    async def authorize(self, timeout: float = 60.0) -> None:
        auth_notify_started = False
        service_notify_started = False
        self._auth_data.state_changed.clear()
        try:
            async with asyncio.timeout(timeout):
                await self._client.start_notify(
                    CHARACTERISTIC_AUTH, self._auth_data.auth_handler
                )
                auth_notify_started = True
                while True:
                    await self._auth_data.state_changed.wait()
                    logger.debug(
                        f"{self._get_internal_name()}: Current state is {self._auth_data.current_state}"
                    )
                    self._auth_data.state_changed.clear()
                    match self._auth_data.current_state:
                        case BonecoAuthState.AUTH_ERROR:
                            raise RuntimeError(
                                f"{self._get_internal_name()}: authorization rejected"
                            )
                        case BonecoAuthState.GOT_NONCE:
                            await self._client.start_notify(
                                CHARACTERISTIC_AUTH_AND_SERVICE,
                                self._auth_data.characteristics_handler,
                            )
                            service_notify_started = True
                            logger.debug(
                                f"{self._get_internal_name()}: Sending challenge response"
                            )
                            await self._client.write_gatt_char(
                                CHARACTERISTIC_AUTH,
                                self._auth_data.get_request_for_auth_level(0),
                            )
                        case BonecoAuthState.CONFIRM_WAITING:
                            logger.info(
                                f"{self._get_internal_name()}: Press device button to confirm"
                            )
                        case BonecoAuthState.CONFIRMED:
                            logger.debug(
                                f"{self._get_internal_name()}: Sending request buffer to device"
                            )
                            await self._client.stop_notify(
                                CHARACTERISTIC_AUTH_AND_SERVICE
                            )
                            service_notify_started = False
                            await self._client.write_gatt_char(
                                CHARACTERISTIC_AUTH,
                                self._auth_data.generate_request_buffer(),
                            )
                        case BonecoAuthState.GOT_DEVICE_KEY:
                            logger.debug(
                                f"{self._get_internal_name()}: Sending auth request"
                            )
                            await self._client.write_gatt_char(
                                CHARACTERISTIC_AUTH,
                                self._auth_data.get_request_for_auth_level(1),
                            )
                        case BonecoAuthState.AUTH_SUCCESS:
                            logger.info(
                                f"{self._get_internal_name()}: Auth finished. Exiting"
                            )
                            break
                        case _:
                            logger.warning(
                                f"{self._get_internal_name()}: Unknown state value"
                            )
        finally:
            if service_notify_started:
                try:
                    await self._client.stop_notify(CHARACTERISTIC_AUTH_AND_SERVICE)
                except Exception as ex:  # noqa: BLE001 - cleanup must preserve the original error
                    logger.warning(
                        "%s: Error stopping service notifications: %s",
                        self._get_internal_name(),
                        ex,
                    )
            if auth_notify_started:
                try:
                    await self._client.stop_notify(CHARACTERISTIC_AUTH)
                except Exception as ex:  # noqa: BLE001 - cleanup must preserve the original error
                    logger.warning(
                        "%s: Error stopping auth notifications: %s",
                        self._get_internal_name(),
                        ex,
                    )

    @require_auth
    async def get_state(self) -> BonecoDeviceState:
        data = await self._client.read_gatt_char(CHARACTERISTIC_DEVICE_STATE)
        return BonecoDeviceState(self._auth_data.name, data)

    @require_auth
    async def set_state(self, state: BonecoDeviceState) -> None:
        await self._client.write_gatt_char(
            CHARACTERISTIC_DEVICE_STATE,
            state.hex_value,
            response=True,
        )

    @require_auth
    async def get_device_info(self) -> BonecoDeviceInfo:
        data = await self._client.read_gatt_char(CHARACTERISTIC_DEVICE_INFO)
        return BonecoDeviceInfo(data)

    @require_auth
    async def get_device_name(self) -> str:
        data = await self._client.read_gatt_char(CHARACTERISTIC_DEVICE_NAME)
        return data.strip(b"\x00").decode()

    def _get_internal_name(self) -> str:
        return f"{self._auth_data.device.name} ({self._auth_data.device.address})"

    async def _ensure_connected(self) -> None:
        if self._client and self._client.is_connected:
            logger.debug(f"{self._get_internal_name()}: Already connected")
            return
        if self.persistent_session:
            raise RuntimeError("Persistent Boneco connection was lost")
        await self.connect()
