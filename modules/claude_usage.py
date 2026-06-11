"""Consulta la quota restante de Claude Code via el endpoint OAuth."""
import json
import logging
import urllib.request
from datetime import datetime

from config.config import CLAUDE_CREDENTIALS_PATH, CLAUDE_USAGE_URL

logger = logging.getLogger(__name__)

WINDOW_LABELS = {
    "five_hour": "Sesión (5 h)",
    "seven_day": "Semana (7 d)",
    "seven_day_opus": "Semana Opus",
    "seven_day_sonnet": "Semana Sonnet",
}


def get_claude_usage():
    """Devuelve la quota de Claude Code como dict.

    Estructura: {"windows": [{"key", "label", "remaining_pct", "resets_at"}],
    "error": str | None}. resets_at es datetime con timezone o None.
    """
    try:
        with open(CLAUDE_CREDENTIALS_PATH) as f:
            token = json.load(f)["claudeAiOauth"]["accessToken"]

        request = urllib.request.Request(
            CLAUDE_USAGE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "anthropic-beta": "oauth-2025-04-20",
            },
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read())

        windows = []
        for key, label in WINDOW_LABELS.items():
            block = data.get(key)
            if not block or block.get("utilization") is None:
                continue
            resets_at = None
            if block.get("resets_at"):
                resets_at = datetime.fromisoformat(block["resets_at"])
            windows.append({
                "key": key,
                "label": label,
                "remaining_pct": max(0.0, 100.0 - float(block["utilization"])),
                "resets_at": resets_at,
            })
        return {"windows": windows, "error": None}
    except Exception as e:
        logger.error("Error consultando uso de Claude Code: %s", e)
        return {"windows": [], "error": str(e)}
