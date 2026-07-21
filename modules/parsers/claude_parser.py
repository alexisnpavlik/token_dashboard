"""Parser de consumo y cuotas para Claude Code (OAuth API y logs locales)."""
import glob
import json
import logging
import os
import urllib.request
from datetime import datetime, timezone

from config.config import CLAUDE_CREDENTIALS_PATH, CLAUDE_LOGS_DIR, CLAUDE_USAGE_URL
from modules.pricing import calculate_cost

logger = logging.getLogger(__name__)

WINDOW_LABELS = {
    "five_hour": "Sesión (5 h)",
    "seven_day": "Semana (7 d)",
    "seven_day_opus": "Semana Opus",
    "seven_day_sonnet": "Semana Sonnet",
}


_quota_cache = {"data": None, "timestamp": 0}

def get_claude_quota() -> dict:
    """Devuelve las cuotas de Claude Code mediante el endpoint OAuth (cached 60s)."""
    now = datetime.now(timezone.utc).timestamp()
    if _quota_cache["data"] and (now - _quota_cache["timestamp"]) < 60:
        return _quota_cache["data"]

    try:
        if not os.path.exists(CLAUDE_CREDENTIALS_PATH):
            return {"windows": [], "error": "Credenciales no encontradas"}

        with open(CLAUDE_CREDENTIALS_PATH) as f:
            token = json.load(f)["claudeAiOauth"]["accessToken"]

        request = urllib.request.Request(
            CLAUDE_USAGE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "anthropic-beta": "oauth-2025-04-20",
            },
        )
        with urllib.request.urlopen(request, timeout=10) as response:
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
        result = {"windows": windows, "error": None}
        _quota_cache["data"] = result
        _quota_cache["timestamp"] = now
        return result
    except Exception as e:
        logger.error("Error consultando cuota OAuth de Claude Code: %s", e)
        if _quota_cache["data"]:
            return _quota_cache["data"]
        return {"windows": [], "error": str(e)}



def parse_claude_logs(max_days: int = 90) -> list:
    """Escanea los logs JSONL de ~/.claude/ y retorna una lista de eventos de consumo."""
    events = []
    if not os.path.exists(CLAUDE_LOGS_DIR):
        return events

    search_pattern = os.path.join(CLAUDE_LOGS_DIR, "**", "*.jsonl")
    log_files = glob.glob(search_pattern, recursive=True)

    cutoff_ts = datetime.now(timezone.utc).timestamp() - (max_days * 86400)

    for filepath in log_files:
        try:
            # Comprobación rápida de fecha de modificación del archivo
            if os.path.getmtime(filepath) < cutoff_ts:
                continue

            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "usage" not in line:
                        continue
                    try:
                        data = json.loads(line)
                        msg = data.get("message")
                        if not isinstance(msg, dict):
                            continue
                        usage = msg.get("usage")
                        if not usage or not isinstance(usage, dict):
                            continue

                        ts_str = data.get("timestamp")
                        if not ts_str:
                            continue
                        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if dt.timestamp() < cutoff_ts:
                            continue

                        model = msg.get("model", "claude-3-5-sonnet")
                        input_tok = usage.get("input_tokens", 0)
                        output_tok = usage.get("output_tokens", 0)
                        cache_write = usage.get("cache_creation_input_tokens", 0)
                        cache_read = usage.get("cache_read_input_tokens", 0)

                        cost = calculate_cost(model, input_tok, output_tok, cache_write, cache_read)

                        events.append({
                            "timestamp": dt,
                            "agent": "Claude Code",
                            "model": model,
                            "input_tokens": input_tok,
                            "output_tokens": output_tok,
                            "cache_write_tokens": cache_write,
                            "cache_read_tokens": cache_read,
                            "total_tokens": input_tok + output_tok + cache_write + cache_read,
                            "cost": cost,
                        })
                    except Exception:
                        continue
        except Exception as e:
            logger.debug("Error leyendo log %s: %s", filepath, e)

    return events
