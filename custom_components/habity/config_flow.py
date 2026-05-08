"""Config flow for Habity integration."""
from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOST, CONF_USE_SSL, DOMAIN


async def validate_device(hass: HomeAssistant, host: str, use_ssl: bool) -> None:
    """Attempt GET /state and verify the response is valid."""
    session = async_get_clientsession(hass, verify_ssl=False)
    scheme = "https" if use_ssl else "http"
    url = f"{scheme}://{host}/state"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
        resp.raise_for_status()
        data = await resp.json()
    if "alarm_enabled" not in data or "next_alarm" not in data:
        raise ValueError("Invalid response from device")


class HabityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Habity."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            use_ssl = True
            try:
                await validate_device(self.hass, host, use_ssl)
            except aiohttp.ClientConnectorError:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientResponseError:
                errors["base"] = "cannot_connect"
            except TimeoutError:
                errors["base"] = "timeout"
            except ValueError:
                errors["base"] = "invalid_response"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Habity ({host})",
                    data={CONF_HOST: host, CONF_USE_SSL: use_ssl},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, description={"suggested_value": "192.168.1.x"}): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "host_example": "192.168.1.100",
            },
        )
