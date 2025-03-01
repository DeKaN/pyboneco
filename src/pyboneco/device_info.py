from __future__ import annotations

from bisect import bisect_left

from .constants import SUPPORTED_DEVICES_BY_TYPE
from .device import BonecoDevice, BonecoOperationModeConfig
from .enums import BonecoOperationMode
from .utils import build_software_version


class BonecoDeviceInfo:
    _device: BonecoDevice | None
    _device_type: int
    _fds_config_error: int
    _fds_log_error: int
    _fds_state_error: int
    _no_water_error: int
    _no_filter_error: int
    _no_base_error: int
    _fan_error: int
    _hum_pack_error: int
    _temp: int | None
    _humidity: int | None
    _particle_value: int | None
    _voc: int | None
    _serial_number: int
    _factory_number: int
    _software_version: str
    _hardware_version: str

    @staticmethod
    def _process_stub_values(value: int, stub_value: int = 255) -> int | None:
        return value if value != stub_value else None

    @staticmethod
    def _calculate_particle_value(value: int) -> int | None:
        v = BonecoDeviceInfo._process_stub_values(value, 65535)
        return (
            None if v is None else bisect_left([0, 120, 324, 672, 1200, 1944, 3840], v)
        )

    # TODO: check all usages later
    @staticmethod
    def transform_particle_value(value: int | None) -> int | None:
        match value:
            case 1 | 2:
                return 1
            case 3 | 4:
                return 2
            case 5:
                return 3
            case 6:
                return 4
            case 7:
                return 5
            case _:
                return None

    def __init__(self, data: bytes) -> None:
        self._device_type = data[0]
        self._device = (
            SUPPORTED_DEVICES_BY_TYPE[self._device_type] if self._device_type else None
        )
        flag = data[1]
        self._fds_config_error = flag & 1
        self._fds_log_error = (flag >> 1) & 1
        self._fds_state_error = (flag >> 2) & 1
        self._no_water_error = (flag >> 3) & 1
        self._no_filter_error = (flag >> 4) & 1
        self._no_base_error = (flag >> 5) & 1
        self._fan_error = (flag >> 6) & 1
        self._hum_pack_error = (flag >> 7) & 1
        self._temp = BonecoDeviceInfo._process_stub_values(data[2])
        self._humidity = BonecoDeviceInfo._process_stub_values(data[3])
        self._particle_value = BonecoDeviceInfo._calculate_particle_value(
            int.from_bytes(data[4:6], byteorder="little")
        )
        self._voc = BonecoDeviceInfo._process_stub_values(
            int.from_bytes(data[6:8], byteorder="little"), 65535
        )
        self._serial_number = int.from_bytes(data[8:14], byteorder="little")
        self._factory_number = int.from_bytes(data[14:16], byteorder="little")
        self._software_version = build_software_version(data[17], data[16])
        v = data[18]
        self._hardware_version = v and f"{(v >> 4) & 15}.{v & 15}" or "1.0"

    @property
    def device(self) -> BonecoDevice | None:
        return self._device

    @property
    def fds_config_error(self) -> bool:
        return self._fds_config_error == 1

    @property
    def fds_log_error(self) -> bool:
        return self._fds_log_error == 1

    @property
    def fds_state_error(self) -> bool:
        return self._fds_state_error == 1

    @property
    def no_water(self) -> bool:
        return self._no_water_error == 1

    @property
    def no_filter(self) -> bool:
        return self._no_filter_error == 1

    @property
    def front_cover_error(self) -> bool:
        return self._no_base_error == 1

    @property
    def fan_error(self) -> bool:
        return False and self._fan_error == 1

    @property
    def hum_pack_error(self) -> bool:
        return self._hum_pack_error == 1

    @property
    def device_type(self) -> str:
        return self.device and self.device.product_name

    @property
    def device_product_id(self) -> str:
        return self.device and self.device.product_id

    @property
    def temperature(self) -> int | None:
        return self._temp

    @property
    def humidity(self) -> int | None:
        return self._humidity

    @property
    def particle_value(self):
        return self.has_particle_sensor and BonecoDeviceInfo.transform_particle_value(
            self._particle_value
        )

    @property
    def voc(self) -> int | None:
        return self._voc

    @property
    def serial_number(self) -> int:
        return self._serial_number

    @property
    def software_version(self) -> str:
        return self._software_version

    @property
    def hardware_version(self) -> str:
        return self._hardware_version

    # TODO: check usage for next 4 properties, maybe replaced by `device` property
    @property
    def supported_operating_modes(
        self,
    ) -> dict[BonecoOperationMode, BonecoOperationModeConfig] | None:
        return self.device and self.device.operating_modes

    @property
    def has_timer_support(self) -> bool:
        return self.device is not None and self.device.device_timer_support

    @property
    def has_history_support(self) -> bool:
        return self.device is not None and self.device.history_support

    @property
    def has_particle_sensor(self) -> bool:
        return self.device is not None and self.device.particle_sensor
