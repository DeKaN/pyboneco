from aiohttp import ClientSession
from .constants import (
    FIRMWARE_TOKEN,
    FIRMWARE_HEADERS,
    FIRMWARE_HOST,
    CHINA_FIRMWARE_HOST,
)


def build_software_version(high: int, low: int) -> str:
    return f"{(high >> 4) & 15}.{high & 15}{(low >> 4) & 15}{low & 15}"


async def check_firmware_update(
    client_session: ClientSession,
    device_name: str,
    device_serial: str,
    current_version: str,
    country_code: str,
) -> tuple[bool, str | None]:
    host = (
        FIRMWARE_HOST
        if country_code != "cn" and "CN" not in device_name
        else CHINA_FIRMWARE_HOST
    )
    url = f"{host}/api/v1/device/firmware?access_token={FIRMWARE_TOKEN}&name={device_name}&version={current_version}&serial={device_serial}&country={country_code}"
    headers = {
        "app-country": country_code,
    }
    async with client_session.get(url=url, headers=FIRMWARE_HEADERS | headers) as resp:
        resp.raise_for_status()
        data = await resp.json()
        return data["success"], data["firmware"]
