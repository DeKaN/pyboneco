"""Regression tests for Boneco device information packets."""

import pytest
from pyboneco import BonecoDeviceInfo


def device_info(raw_particles=0, flags=0, device_type=13):
    payload = bytearray(20)
    payload[0] = device_type
    payload[1] = flags
    payload[2:4] = bytes([21, 50])
    payload[4:6] = raw_particles.to_bytes(2, "little")
    payload[6:8] = b"\xff\xff"
    return BonecoDeviceInfo(payload)


@pytest.mark.parametrize("flags", [0, 0x01, 0x3F, 0x40, 0x80, 0xBF, 0xFF])
def test_fan_error_uses_only_the_fan_error_bit(flags):
    assert device_info(flags=flags).fan_error is bool(flags & 0x40)


@pytest.mark.parametrize(
    ("raw", "level"),
    [
        (0, 1),
        (1, 1),
        (24, 1),
        (25, 1),
        (120, 1),
        (121, 1),
        (324, 1),
        (325, 2),
        (672, 2),
        (673, 2),
        (1200, 2),
        (1201, 3),
        (1944, 3),
        (1945, 4),
        (3840, 4),
        (3841, 5),
        (6600, 5),
        (6601, 5),
        (65534, 5),
        (65535, None),
    ],
)
def test_air_quality_levels_cover_all_boundaries(raw, level):
    info = device_info(raw)
    assert info.particle_value == level
    assert info.particle_raw == (None if raw == 65535 else raw)


def test_zero_is_valid_but_missing_data_is_unknown():
    assert device_info(0).particle_value == 1
    assert device_info(65535).particle_value is None


def test_device_without_particle_sensor_has_no_particle_reading():
    info = device_info(1201, device_type=2)  # W400
    assert info.particle_value is None
    assert info.particle_raw is None


def test_little_endian_reading_retains_both_bytes():
    info = device_info(0x1234)
    assert info.particle_raw == 4660
    assert info.particle_value == 5
