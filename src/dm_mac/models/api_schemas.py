"""Request and response models for API endpoint validation."""

from typing import List

from pydantic import BaseModel


class MachineUpdateRequest(BaseModel):
    """Request body for POST /api/machine/update."""

    machine_name: str
    oops: bool
    rfid_value: str
    uptime: float
    wifi_signal_db: float
    wifi_signal_percent: float
    internal_temperature_c: float
    amps: float = 0.0


class MachineUpdateResponse(BaseModel):
    """Response body for POST /api/machine/update (200)."""

    relay: bool
    display: str
    oops_led: bool
    status_led_rgb: List[float]
    status_led_brightness: float


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool


class ErrorResponse(BaseModel):
    """Generic error response."""

    error: str


class ReloadUsersResponse(BaseModel):
    """Response body for POST /api/reload-users (200)."""

    removed: int
    updated: int
    added: int


class ApiIndexResponse(BaseModel):
    """Response body for GET /api/."""

    message: str
