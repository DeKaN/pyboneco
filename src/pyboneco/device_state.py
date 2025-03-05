from __future__ import annotations

from datetime import datetime, timedelta

from .constants import (
    MIN_HUMIDITY,
    MAX_HUMIDITY,
    MIN_LED_BRIGHTNESS,
    MAX_LED_BRIGHTNESS,
)
from .device import BonecoDevice
from .enums import BonecoOperationMode, BonecoModeStatus, BonecoTimerStatus


class BonecoDeviceState:
    FAN_MODE_CURRENT_VALUE = 0
    FAN_MODE_TARGET_VALUE = 1

    AIR_FAN_DEVICE_FAN_MAX_VALUE = 32
    OTHER_DEVICE_FAN_MAX_VALUE = 6
    RESET_DATE_BYTES = b"\xff\xff\xff\xff"

    _is_air_fan_device: bool
    _has_service_operating_counter: bool
    _operating_mode: BonecoOperationMode
    _mode_status: BonecoModeStatus
    _fan: int
    _fan_mode: int
    _timer: int
    _always_history_active: int
    _lock: int
    _on_off: int
    __unused: int
    _target_humidity: int
    _change_filter: int
    _change_iss: int
    _clean: int
    _change_water: int
    _reminder_filter_counter: int | None
    _reminder_iss_counter: int | None
    _reminder_clean_counter: int | None
    _reminder_filter_date: int | None
    _reminder_iss_date: int | None
    _reminder_clean_date: int | None
    _on_off_timer_hours: int
    _clean_mode_support: int
    _on_off_timer_status: BonecoTimerStatus
    _on_off_timer_minutes: int
    _min_led_brightness: int
    _max_led_brightness: int

    def __init__(self, local_name: str, data: bytes) -> None:
        self._is_air_fan_device = BonecoDevice.is_device_air_fan(local_name)
        self._has_service_operating_counter = (
            BonecoDevice.has_service_operating_counter(local_name)
        )
        flag = data[0]
        if self.is_air_fan:
            self._operating_mode = BonecoOperationMode.NONE
            self._mode_status = BonecoModeStatus.CUSTOM
            self._fan = flag & 127
            self._fan_mode = 0
        else:
            self._operating_mode = BonecoOperationMode(flag & 3)
            self._mode_status = BonecoModeStatus((flag >> 2) & 3)
            self._fan = (flag >> 4) & 7
            self._fan_mode = (flag >> 7) & 1
        flag = data[1]
        self._timer = flag & 1
        self._always_history_active = (flag >> 1) & 1
        self._lock = (flag >> 2) & 1
        self._on_off = (flag >> 3) & 1
        self.__unused = (flag >> 4) & 15
        self._target_humidity = 0 if self.is_air_fan else data[2]
        flag = data[3]
        self._change_filter = (flag >> 4) & 1
        self._change_iss = (flag >> 5) & 1
        self._clean = (flag >> 6) & 1
        self._change_water = (flag >> 7) & 1
        filter_data = int.from_bytes(data[4:8], byteorder="little")
        iss_data = int.from_bytes(data[8:12], byteorder="little")
        clean_data = int.from_bytes(data[12:16], byteorder="little")
        if self.has_service_operating_counter:
            self._reminder_filter_counter = filter_data
            self._reminder_iss_counter = iss_data
            self._reminder_clean_counter = clean_data
            self._reminder_filter_date = 0
            self._reminder_iss_date = 0
            self._reminder_clean_date = 0
        else:
            self._reminder_filter_counter = None
            self._reminder_iss_counter = None
            self._reminder_clean_counter = None
            self._reminder_filter_date = filter_data
            self._reminder_iss_date = iss_data
            self._reminder_clean_date = clean_data
        flag = data[16]
        self._on_off_timer_hours = flag & 31
        self._clean_mode_support = (flag >> 5) & 1
        self._on_off_timer_status = BonecoTimerStatus((flag >> 6) & 3)
        self._on_off_timer_minutes = data[17]
        self._min_led_brightness = data[18]
        self._max_led_brightness = data[19]

    # TODO: private or shared function?
    @staticmethod
    def get_date_with_minute_offset(days: int, minutes: int) -> datetime:
        return datetime.now().astimezone() + timedelta(days=days, minutes=-minutes)

    @staticmethod
    def get_date_with_hour_offset(days: int, hours: int):
        return datetime.now().astimezone() + timedelta(days=days, hours=-hours)

    @property
    def is_air_fan(self) -> bool:
        return self._is_air_fan_device

    @property
    def has_service_operating_counter(self) -> bool:
        return self._has_service_operating_counter

    @property
    def operating_mode(self) -> BonecoOperationMode:
        return self._operating_mode

    @operating_mode.setter
    def operating_mode(self, value: BonecoOperationMode) -> None:
        self._operating_mode = value

    @property
    def mode_status(self) -> BonecoModeStatus:
        return self._mode_status

    @mode_status.setter
    def mode_status(self, value: BonecoModeStatus) -> None:
        self._mode_status = value

    @property
    def fan_mode(self) -> int:
        return self._fan_mode

    @property
    def fan_level(self) -> int:
        return self._fan

    @fan_level.setter
    def fan_level(self, value: int) -> None:
        self._fan = min(
            value,
            BonecoDeviceState.AIR_FAN_DEVICE_FAN_MAX_VALUE
            if self.is_air_fan
            else BonecoDeviceState.OTHER_DEVICE_FAN_MAX_VALUE,
        )
        if self.mode_status != BonecoModeStatus.CUSTOM:
            self.mode_status = BonecoModeStatus.CUSTOM

    @property
    def is_always_history_active(self) -> bool:
        return self._always_history_active == 1

    @is_always_history_active.setter
    def is_always_history_active(self, value: bool) -> None:
        self._always_history_active = 1 if value else 0

    @property
    def is_locked(self) -> bool:
        return self._lock == 1

    @is_locked.setter
    def is_locked(self, value: bool) -> None:
        self._lock = 1 if value else 0

    @property
    def is_enabled(self) -> bool:
        return self._on_off == 1

    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        self._on_off = 1 if value else 0

    @property
    def target_humidity(self) -> int:
        return self._target_humidity

    @target_humidity.setter
    def target_humidity(self, value: int) -> None:
        if MIN_HUMIDITY <= value <= MAX_HUMIDITY:
            self._target_humidity = value
        else:
            raise ValueError("Invalid target humidity, it should be in [30..70]")

    @property
    def has_clean_mode_support(self) -> bool:
        return self._clean_mode_support == 1

    @property
    def is_change_water_needed(self) -> bool:
        return not self.has_clean_mode_support and self._change_water == 1

    def _has_date(self, date_value: datetime | None) -> bool:
        return self.has_service_operating_counter or date_value

    def _get_date(
        self, timestamp: int | None, counter: int | None, interval: int | None = None
    ) -> datetime | None:
        if not self.has_service_operating_counter:
            return timestamp and datetime.fromtimestamp(timestamp).astimezone() or None
        if not interval:
            raise ValueError("Interval is required for devices with service counter")
        return BonecoDeviceState.get_date_with_minute_offset(interval, counter)

    def _set_date_prepare(self, value: datetime | None, name: str) -> int | None:
        if self.has_service_operating_counter and value is not None:
            raise ValueError(
                f"Device has service counter support, can't set reminder {name} date. You can only reset the counter."
            )
        elif not self.has_service_operating_counter and value is None:
            raise ValueError(
                f"Device has no service counter support, can't set reminder {name} date. "
                f"You can only set reminder date."
            )
        return value and int(value.astimezone().timestamp())

    @property
    def has_reminder_filter_date(self) -> bool:
        return self._has_date(self._reminder_filter_date)

    def get_reminder_filter_date(self, interval: int | None = None) -> datetime | None:
        return self._get_date(
            self._reminder_filter_date, self._reminder_filter_counter, interval
        )

    def set_reminder_filter_date(self, value: datetime | None) -> None:
        self._reminder_filter_date = self._set_date_prepare(value, "filter")

    @property
    def has_reminder_iss_date(self) -> bool:
        return self._has_date(self._reminder_iss_date)

    def get_reminder_iss_date(self, interval: int | None = None) -> datetime | None:
        return self._get_date(
            self._reminder_iss_date, self._reminder_iss_counter, interval
        )

    def set_reminder_iss_date(self, value: datetime | None) -> None:
        self._reminder_iss_date = self._set_date_prepare(value, "iss")

    @property
    def has_reminder_clean_date(self) -> bool:
        return self._has_date(self._reminder_clean_date)

    def get_reminder_clean_date(self, interval: int | None = None) -> datetime | None:
        return self._get_date(
            self._reminder_clean_date, self._reminder_clean_counter, interval
        )

    def set_reminder_clean_date(self, value: datetime | None) -> None:
        self._reminder_clean_date = self._set_date_prepare(value, "clean")

    @property
    def on_off_timer_status(self) -> BonecoTimerStatus:
        return self._on_off_timer_status

    @on_off_timer_status.setter
    def on_off_timer_status(self, value: BonecoTimerStatus) -> None:
        if value == BonecoTimerStatus.RESERVED:
            raise ValueError("Not supported value")
        self._on_off_timer_status = value

    @property
    def on_of_timer_hours(self) -> int:
        return self._on_off_timer_hours

    @on_of_timer_hours.setter
    def on_of_timer_hours(self, value: int) -> None:
        if 0 <= value <= 24:
            self._on_off_timer_hours = value
        else:
            raise ValueError("Invalid hours value")

    @property
    def on_of_timer_minutes(self) -> int:
        return self._on_off_timer_minutes

    @on_of_timer_minutes.setter
    def on_of_timer_minutes(self, value: int) -> None:
        if 0 <= value <= 59:
            self._on_off_timer_minutes = value
        else:
            raise ValueError("Invalid minutes value")

    @property
    def min_led_brightness(self) -> int:
        return self._min_led_brightness

    @min_led_brightness.setter
    def min_led_brightness(self, value: int) -> None:
        if MIN_LED_BRIGHTNESS <= value <= MAX_LED_BRIGHTNESS:
            self._min_led_brightness = value
        else:
            raise ValueError("Invalid minimum brightness value")

    @property
    def max_led_brightness(self) -> int:
        return self._max_led_brightness

    @max_led_brightness.setter
    def max_led_brightness(self, value: int) -> None:
        if MIN_LED_BRIGHTNESS <= value <= MAX_LED_BRIGHTNESS:
            self._max_led_brightness = value
        else:
            raise ValueError("Invalid maximum brightness value")

    def _prepare_reminder_date(self, value: int | None) -> bytes:
        if self.has_service_operating_counter:
            if value is None:
                return BonecoDeviceState.RESET_DATE_BYTES
        else:
            return value.to_bytes(4, byteorder="little")

    @property
    def hex_value(self) -> bytes:
        byte_fan = (self.fan_mode & 1) << 7
        if self.is_air_fan:
            byte_fan |= self.fan_level & 127
        else:
            byte_fan |= (
                ((self.fan_level & 7) << 4)
                | ((self.mode_status.value & 3) << 2)
                | (self.operating_mode & 3)
            )
        byte_props = (
            ((self.__unused & 15) << 4)
            | ((self._on_off & 1) << 3)
            | ((self._lock & 1) << 2)
            | ((self._always_history_active & 1) << 1)
            | (self._timer & 1)
        )

        if (
            filter_data := self._prepare_reminder_date(self._reminder_filter_date)
        ) == BonecoDeviceState.RESET_DATE_BYTES:
            self._reminder_filter_date = 0
        if (
            iss_data := self._prepare_reminder_date(self._reminder_iss_date)
        ) == BonecoDeviceState.RESET_DATE_BYTES:
            self._reminder_filter_date = 0
        if (
            clean_data := self._prepare_reminder_date(self._reminder_clean_date)
        ) == BonecoDeviceState.RESET_DATE_BYTES:
            self._reminder_filter_date = 0
        data = (
            bytes(
                [
                    byte_fan,
                    byte_props,
                    self.target_humidity,
                    # self._change_filter, self._change_iss, self._clean, self._change_water parsed from the next byte
                    0,
                ]
            )
            + filter_data
            + iss_data
            + clean_data
            + bytes(
                [
                    # self._clean_mode_support parsed from shifting to 5 the next byte
                    ((self.on_off_timer_status.value & 3) << 6)
                    | ((0 & 1) << 5)
                    | (self._on_off_timer_hours & 31),
                    self.on_of_timer_minutes,
                    self.min_led_brightness,
                    self.max_led_brightness,
                ]
            )
        )
        return data
