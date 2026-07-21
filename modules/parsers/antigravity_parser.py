"""Parser de consumo y cuotas para Antigravity y Gemini CLI."""
import glob
import json
import logging
import os
import subprocess
from datetime import datetime, timezone

from config.config import ANTIGRAVITY_LOGS_DIR, ANTIGRAVITY_USAGE_BIN
from modules.pricing import calculate_cost

logger = logging.getLogger(__name__)


_antigravity_quota_cache = {"data": None, "timestamp": 0}


def get_antigravity_quota() -> dict:
    """Devuelve la quota de Antigravity llamando al CLI antigravity-usage (cached 60s)."""
    now = datetime.now(timezone.utc).timestamp()
    if _antigravity_quota_cache["data"] and (now - _antigravity_quota_cache["timestamp"]) < 60:
        return _antigravity_quota_cache["data"]

    try:
        result = subprocess.run(
            [ANTIGRAVITY_USAGE_BIN, "quota", "--json"],
            capture_output=True, text=True, timeout=15,
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
        res = {"models": models, "email": data.get("email"), "error": None}
        _antigravity_quota_cache["data"] = res
        _antigravity_quota_cache["timestamp"] = now
        return res
    except Exception as e:
        logger.error("Error consultando cuota de Antigravity: %s", e)
        if _antigravity_quota_cache["data"]:
            return _antigravity_quota_cache["data"]
        return {"models": [], "email": None, "error": str(e)}



def parse_antigravity_logs(max_days: int = 90) -> list:
    """Escanea archivos de brain/logs en ~/.gemini/ para calcular consumo."""
    events = []
    if not os.path.exists(ANTIGRAVITY_LOGS_DIR):
        return events

    search_pattern = os.path.join(ANTIGRAVITY_LOGS_DIR, "**", "*.json")
    files = glob.glob(search_pattern, recursive=True)
    cutoff_ts = datetime.now(timezone.utc).timestamp() - (max_days * 86400)

    for filepath in files:
        if "metadata" not in filepath and "transcript" not in filepath:
            continue
        try:
            mtime = os.path.getmtime(filepath)
            if mtime < cutoff_ts:
                continue

            dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(50000)
                if not content:
                    continue

                # Estimación basada en longitud del contenido o campos de tokens si existen
                char_count = len(content)
                est_tokens = max(100, char_count // 4)
                input_tok = int(est_tokens * 0.7)
                output_tok = int(est_tokens * 0.3)
                model = "gemini-3.6-flash"

                cost = calculate_cost(model, input_tok, output_tok)
                events.append({
                    "timestamp": dt,
                    "agent": "Antigravity",
                    "model": model,
                    "input_tokens": input_tok,
                    "output_tokens": output_tok,
                    "cache_write_tokens": 0,
                    "cache_read_tokens": 0,
                    "total_tokens": est_tokens,
                    "cost": cost,
                })
        except Exception as e:
            logger.debug("Error procesando log de Antigravity %s: %s", filepath, e)

    return events
