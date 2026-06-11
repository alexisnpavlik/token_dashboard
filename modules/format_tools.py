"""Utilidades de formato para fechas de reset y porcentajes."""
from datetime import datetime, timezone


def format_reset(resets_at):
    """Formatea la hora de reset como 'HH:MM (en Xh Ym)' en hora local."""
    if resets_at is None:
        return "—"
    local = resets_at.astimezone()
    delta = resets_at - datetime.now(timezone.utc)
    total_minutes = max(0, int(delta.total_seconds() // 60))
    hours, minutes = divmod(total_minutes, 60)
    if hours >= 24:
        days, hours = divmod(hours, 24)
        relative = f"en {days}d {hours}h"
    elif hours:
        relative = f"en {hours}h {minutes}m"
    else:
        relative = f"en {minutes}m"
    return f"{local.strftime('%d/%m %H:%M')} ({relative})"


def format_pct(remaining_pct):
    """Formatea el porcentaje restante con cero decimales."""
    return f"{remaining_pct:.0f}%"


def quota_level(remaining_pct):
    """Devuelve el nivel según el porcentaje restante: good/warn/alert/low."""
    if remaining_pct >= 50:
        return "good"
    if remaining_pct >= 25:
        return "warn"
    if remaining_pct >= 10:
        return "alert"
    return "low"


def level_emoji(remaining_pct):
    """Devuelve el círculo de color según el porcentaje restante."""
    return {"good": "🟢", "warn": "🟡", "alert": "🟠", "low": "🔴"}[
        quota_level(remaining_pct)
    ]
