from .device import (
    BonecoAirFanDevice,
    BonecoSimpleClimateDevice,
    BonecoHumidifierDevice,
    BonecoTopClimateDevice,
    BonecoDevice,
)
from .enums import BonecoDeviceClass

BONECO_MANUFACTER_ID = 0x0299
BONECO_DATA_MARKER = 66

MIN_HUMIDITY = 30
MAX_HUMIDITY = 70
MIN_LED_BRIGHTNESS = 0
MAX_LED_BRIGHTNESS = 100
AIR_FAN_DEVICE_FAN_MAX_VALUE = 32
OTHER_DEVICE_FAN_MAX_VALUE = 6

SERVICE_ID_DEVICE_INFORMATION = "180A"
CHARACTERISTIC_MANUFACTURER_NAME_STRING = "2A29"
CHARACTERISTIC_MODEL_NUMBER_STRING = "2A24"
CHARACTERISTIC_SERIAL_NUMBER_STRING = "2A25"
CHARACTERISTIC_HARDWARE_REVISION_STRING = "2A27"
CHARACTERISTIC_FIRMWARE_REVISION_STRING = "2A26"
CHARACTERISTIC_SOFTWARE_REVISION_STRING = "2A28"
CHARACTERISTIC_SYTEM_ID = "2A23"
SERVICE_ID_DEVICE_STATE = "fdce1234-1013-4120-b919-1dbb32a2d132"
CHARACTERISTIC_DEVICE_STATE = "fdce2345-1013-4120-b919-1dbb32a2d132"
CHARACTERISTIC_DEVICE_INFO = "fdce2346-1013-4120-b919-1dbb32a2d132"
CHARACTERISTIC_DEVICE_NAME = "fdce2349-1013-4120-b919-1dbb32a2d132"
CHARACTERISTIC_DEVICE_TIMER = "fdce2350-1013-4120-b919-1dbb32a2d132"
CHARACTERISTIC_DEVICE_HISTORY = "fdce2351-1013-4120-b919-1dbb32a2d132"
SERVICE_ID_APP_AUTH = "fdce1236-1013-4120-b919-1dbb32a2d132"
CHARACTERISTIC_AUTH = "fdce2347-1013-4120-b919-1dbb32a2d132"
CHARACTERISTIC_AUTH_AND_SERVICE = "fdce2348-1013-4120-b919-1dbb32a2d132"

FIRMWARE_HOST = "https://boneco-fw.webulos.com"
CHINA_FIRMWARE_HOST = "https://fw.boneco.com.cn"
FIRMWARE_TOKEN = "mp2feQtdrteEGiZ9CWeJUsC73qyeHJb9"

# Using Android app with version "4.70", build number "202" at Android 15 (API level 35)
FIRMWARE_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "app-platform": "Android",
    "app-version": "4.70.202",
    "app-build-number": "202",
    "app-api": "35",
    "app-system-version": "15",
}

SUPPORTED_DEVICES: list[BonecoDevice] = [
    BonecoSimpleClimateDevice(1, "H300", "H300"),
    BonecoHumidifierDevice(2, "W400", "W400"),
    BonecoSimpleClimateDevice(3, "H400", "H400"),
    BonecoSimpleClimateDevice(3, "H500", "H500"),
    BonecoAirFanDevice(5, "X500", "X500"),  # Google doesn't know about it
    BonecoSimpleClimateDevice(6, "H600", "H600"),
    BonecoSimpleClimateDevice(7, "H300", "H300 CN"),
    BonecoHumidifierDevice(8, "W400", "W400 CN"),
    BonecoSimpleClimateDevice(9, "H400", "H400 CN"),
    # device with type 10 is missed
    BonecoAirFanDevice(11, "F225", "F2X5"),
    BonecoAirFanDevice(11, "F225", "F225"),
    BonecoAirFanDevice(12, "F235", "F235"),
    BonecoTopClimateDevice(13, "H700", "H700"),
    BonecoTopClimateDevice(14, "H700", "H700 US"),
    BonecoSimpleClimateDevice(15, "H320", "H320"),
    BonecoSimpleClimateDevice(16, "H320", "H320 CN"),
]

SUPPORTED_DEVICES_BY_TYPE: dict[int, BonecoDevice] = {
    d.device_type: d for d in SUPPORTED_DEVICES
}

SUPPORTED_DEVICE_CLASSES_BY_MODEL: dict[str, BonecoDeviceClass] = {
    d.product_name: d.device_class for d in SUPPORTED_DEVICES
}
