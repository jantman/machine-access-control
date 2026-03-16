"""Request and response models for API endpoint validation."""

from typing import List

from pydantic import BaseModel
from pydantic import Field


class MachineUpdateRequest(BaseModel):
    """Request body for POST /api/machine/update."""

    machine_name: str = Field(description="Name of the machine sending the update.")
    oops: bool = Field(description="Whether the oops button is pressed.")
    rfid_value: str = Field(
        description="Value of the RFID fob/card currently present, "
        "or empty string if none. ESPHome strips leading zeroes; "
        "the server left-pads to 10 characters."
    )
    uptime: float = Field(description="Uptime of the ESP32 (MCU) in seconds.")
    wifi_signal_db: float = Field(description="WiFi signal strength in dB.")
    wifi_signal_percent: float = Field(description="WiFi signal strength in percent.")
    internal_temperature_c: float = Field(
        description="Internal temperature of the ESP32 in °C."
    )
    amps: float = Field(
        default=0.0,
        description="Amperage from the current clamp ammeter, if present.",
    )


class MachineUpdateResponse(BaseModel):
    """Response body for POST /api/machine/update (200)."""

    relay: bool = Field(description="Desired relay state (true = machine enabled).")
    display: str = Field(description="Text to show on the MCU's LCD display.")
    oops_led: bool = Field(description="Whether the oops LED should be lit.")
    status_led_rgb: List[float] = Field(
        description="RGB values for the status LED as [red, green, blue] (0.0-1.0)."
    )
    status_led_brightness: float = Field(
        description="Brightness of the status LED (0.0-1.0)."
    )


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = Field(description="Whether the operation succeeded.")


class ErrorResponse(BaseModel):
    """Generic error response."""

    error: str = Field(description="Error message describing what went wrong.")


class ReloadUsersResponse(BaseModel):
    """Response body for POST /api/reload-users (200)."""

    removed: int = Field(description="Number of users removed.")
    updated: int = Field(description="Number of users updated.")
    added: int = Field(description="Number of users added.")


class ApiIndexResponse(BaseModel):
    """Response body for GET /api/."""

    message: str = Field(description="Placeholder message.")
