"""Parser de consumo para Aider CLI (historial de chat e input)."""
import glob
import logging
import os
from datetime import datetime, timezone

from config.config import AIDER_LOGS_DIR
from modules.pricing import calculate_cost

logger = logging.getLogger(__name__)


def parse_aider_logs(max_days: int = 90) -> list:
    """Escanea archivos de historial de Aider para estimar tokens consumidos."""
    events = []
    if not os.path.exists(AIDER_LOGS_DIR):
        return events

    cutoff_ts = datetime.now(timezone.utc).timestamp() - (max_days * 86400)
    history_files = glob.glob(os.path.join(AIDER_LOGS_DIR, "**", ".aider.chat.history.md"), recursive=True)

    for filepath in history_files:
        try:
            mtime = os.path.getmtime(filepath)
            if mtime < cutoff_ts:
                continue

            dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if content:
                # Estimación aproximada de tokens basados en el tamaño de caracteres
                char_count = len(content)
                total_tok = max(200, char_count // 4)
                input_tok = int(total_tok * 0.75)
                output_tok = int(total_tok * 0.25)
                model = "claude-3-5-sonnet"
                cost = calculate_cost(model, input_tok, output_tok)

                events.append({
                    "timestamp": dt,
                    "agent": "Aider",
                    "model": model,
                    "input_tokens": input_tok,
                    "output_tokens": output_tok,
                    "cache_write_tokens": 0,
                    "cache_read_tokens": 0,
                    "total_tokens": total_tok,
                    "cost": cost,
                })
        except Exception as e:
            logger.debug("Error procesando log de Aider %s: %s", filepath, e)

    return events
