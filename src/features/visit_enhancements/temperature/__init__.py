"""Bloco de condições ambientais (temperatura/clima)."""
from .temperature_service import (
    capture_and_save_external_weather,
    render_temperature_block,
    save_manual_weather,
)

__all__ = ["capture_and_save_external_weather", "render_temperature_block", "save_manual_weather"]
