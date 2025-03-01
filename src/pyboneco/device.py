from typing import Optional

from .enums import BonecoOperationMode, BonecoModeStatus, BonecoDeviceClass

BonecoOperationModeConfig = Optional[dict[BonecoModeStatus, bool]]


class BonecoDevice:
    device_type: int
    device_class: BonecoDeviceClass
    product_id: str
    product_name: str
    operating_modes: dict[BonecoOperationMode, BonecoOperationModeConfig]
    device_timer_support: bool
    history_support: bool
    particle_sensor: bool

    @staticmethod
    def is_device_air_fan(model: str):
        return model in ["F225", "F235"]

    @staticmethod
    def has_service_operating_counter(model: str):
        return model in ["H700", "H700 US"]

    @staticmethod
    def has_device_history_support(model: str):
        return model in ["H700", "H700 US"]

    def __init__(
        self,
        device_type: int,
        device_class: BonecoDeviceClass,
        product_id: str,
        product_name,
        operating_modes: dict[BonecoOperationMode, BonecoOperationModeConfig],
        device_timer_support: bool = False,
        history_support: bool = False,
        particle_sensor: bool = False,
    ) -> None:
        self.device_type = device_type
        self.device_class = device_class
        self.product_id = product_id
        self.product_name = product_name
        self.operating_modes = operating_modes
        self.device_timer_support = device_timer_support
        self.history_support = history_support
        self.particle_sensor = particle_sensor


class BonecoAirFanDevice(BonecoDevice):
    def __init__(self, device_type: int, product_id: str, product_name: str) -> None:
        super().__init__(
            device_type,
            BonecoDeviceClass.FAN,
            product_id,
            product_name,
            dict(
                {
                    BonecoOperationMode.HUMIDIFIER: None,
                    BonecoOperationMode.PURIFIER: None,
                    BonecoOperationMode.HYBRID: None,
                }
            ),
        )


class BonecoHumidifierDevice(BonecoDevice):
    def __init__(self, device_type: int, product_id: str, product_name: str) -> None:
        super().__init__(
            device_type,
            BonecoDeviceClass.HUMIDIFIER,
            product_id,
            product_name,
            dict(
                {
                    BonecoOperationMode.HUMIDIFIER: {
                        BonecoModeStatus.CUSTOM: True,
                        BonecoModeStatus.AUTO: True,
                        BonecoModeStatus.BABY: True,
                        BonecoModeStatus.SLEEP: True,
                    },
                    BonecoOperationMode.PURIFIER: None,
                    BonecoOperationMode.HYBRID: None,
                }
            ),
        )


class BonecoSimpleClimateDevice(BonecoDevice):
    def __init__(self, device_type: int, product_id: str, product_name: str) -> None:
        super().__init__(
            device_type,
            BonecoDeviceClass.SIMPLE_CLIMATE,
            product_id,
            product_name,
            dict(
                {
                    BonecoOperationMode.HUMIDIFIER: {
                        BonecoModeStatus.CUSTOM: True,
                        BonecoModeStatus.AUTO: True,
                        BonecoModeStatus.BABY: True,
                        BonecoModeStatus.SLEEP: True,
                    },
                    BonecoOperationMode.PURIFIER: {
                        BonecoModeStatus.CUSTOM: True,
                        BonecoModeStatus.AUTO: False,
                        BonecoModeStatus.BABY: False,
                        BonecoModeStatus.SLEEP: False,
                    },
                    BonecoOperationMode.HYBRID: {
                        BonecoModeStatus.CUSTOM: True,
                        BonecoModeStatus.AUTO: True,
                        BonecoModeStatus.BABY: True,
                        BonecoModeStatus.SLEEP: True,
                    },
                }
            ),
        )


class BonecoTopClimateDevice(BonecoDevice):
    def __init__(self, device_type: int, product_id: str, product_name: str) -> None:
        super().__init__(
            device_type,
            BonecoDeviceClass.TOP_CLIMATE,
            product_id,
            product_name,
            dict(
                {
                    BonecoOperationMode.HUMIDIFIER: {
                        BonecoModeStatus.CUSTOM: True,
                        BonecoModeStatus.AUTO: True,
                        BonecoModeStatus.BABY: True,
                        BonecoModeStatus.SLEEP: True,
                    },
                    BonecoOperationMode.PURIFIER: {
                        BonecoModeStatus.CUSTOM: True,
                        BonecoModeStatus.AUTO: True,
                        BonecoModeStatus.BABY: True,
                        BonecoModeStatus.SLEEP: True,
                    },
                    BonecoOperationMode.HYBRID: {
                        BonecoModeStatus.CUSTOM: True,
                        BonecoModeStatus.AUTO: True,
                        BonecoModeStatus.BABY: True,
                        BonecoModeStatus.SLEEP: True,
                    },
                }
            ),
            device_timer_support=True,
            history_support=True,
            particle_sensor=True,
        )
