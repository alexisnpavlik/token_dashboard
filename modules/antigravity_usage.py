"""Consulta la quota restante de Antigravity via la CLI antigravity-usage."""
import json
import logging
import subprocess
from datetime import datetime

from config.config import ANTIGRAVITY_USAGE_BIN

logger = logging.getLogger(__name__)


def get_antigravity_usage():
    """Devuelve la quota de Antigravity como dict.

    Estructura: {"models": [{"label", "remaining_pct", "resets_at",
    "is_exhausted"}], "email": str | None, "error": str | None}.
    Excluye modelos solo-autocomplete. resets_at es datetime o None.
    """
    try:
        result = subprocess.run(
            [ANTIGRAVITY_USAGE_BIN, "quota", "--json"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "exit code != 0")
        data = json.loads(result.stdout)

        models = []
        for m in data.get("models", []):
            if m.get("isAutocompleteOnly"):
                continue
            resets_at = None
            if m.get("resetTime"):
                resets_at = datetime.fromisoformat(
                    m["resetTime"].replace("Z", "+00:00")
                )
            models.append({
                "label": m.get("label", m.get("modelId", "?")),
                "remaining_pct": float(m.get("remainingPercentage", 0)) * 100.0,
                "resets_at": resets_at,
                "is_exhausted": bool(m.get("isExhausted")),
            })
        return {"models": models, "email": data.get("email"), "error": None}
    except Exception as e:
        logger.error("Error consultando uso de Antigravity: %s", e)
        return {"models": [], "email": None, "error": str(e)}
