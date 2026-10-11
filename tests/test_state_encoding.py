"""Regression tests for Boneco state write packets."""

import copy

import pytest
from pyboneco import BonecoDeviceState


def h700_state() -> BonecoDeviceState:
    # Nonzero counters, service flags and clean-mode bit expose unrelated changes.
    return BonecoDeviceState(
        "H700", bytes.fromhex("310a46d57856341234120000efcdab0065070164")
    )


def test_brightness_write_preserves_flags_without_resetting_counters():
    state = h700_state()
    state.max_led_brightness = 90

    # H700 writes: bytes 4..15 are zero unless a counter reset was requested;
    # service flags (byte 3) and clean-mode bit (byte 16) are preserved.
    assert state.hex_value == bytes.fromhex("310a46d50000000000000000000000006507015a")


@pytest.mark.parametrize(("kind", "start"), [("filter", 4), ("iss", 8), ("clean", 12)])
def test_reset_only_encodes_the_requested_counter(kind, start):
    state = h700_state()
    getattr(state, f"set_reminder_{kind}_date")(None)
    expected = bytearray(12)
    expected[start - 4 : start] = b"\xff" * 4
    before = copy.deepcopy(vars(state))

    assert state.hex_value[4:16] == expected
    assert state.hex_value[4:16] == expected
    assert vars(state) == before


def test_lower_maximum_also_lowers_minimum():
    state = h700_state()
    state.min_led_brightness = 100
    state.max_led_brightness = 90
    assert state.hex_value[18:20] == bytes([90, 90])


def test_higher_minimum_also_raises_maximum():
    state = h700_state()
    state.max_led_brightness = 20
    state.min_led_brightness = 40
    assert state.hex_value[18:20] == bytes([40, 40])


@pytest.mark.parametrize("attribute", ["min_led_brightness", "max_led_brightness"])
@pytest.mark.parametrize("value", [-1, 101])
def test_brightness_rejects_out_of_range_values(attribute, value):
    state = h700_state()
    with pytest.raises(ValueError):
        setattr(state, attribute, value)


def test_devices_with_dates_keep_their_reminder_values():
    raw = bytes.fromhex("310a46d57856341234120000efcdab0065070164")
    state = BonecoDeviceState("W400", raw)
    state.max_led_brightness = 90
    assert state.hex_value == raw[:19] + bytes([90])
