"""Parser de consumo para Roo Code y Cline (carpetas de tareas de extensiones)."""
import glob
import json
import logging
import os
from datetime import datetime, timezone

from config.config import ROO_CLINE_LOGS_DIR
from modules.pricing import calculate_cost

logger = logging.getLogger(__name__)


def parse_roo_cline_logs(max_days: int = 90) -> list:
    """Escanea las tareas JSON de Roo Code y Cline."""
    events = []
    if not os.path.exists(ROO_CLINE_LOGS_DIR):
        return events

    cutoff_ts = datetime.now(timezone.utc).timestamp() - (max_days * 86400)
    task_files = glob.glob(os.path.join(ROO_CLINE_LOGS_DIR, "**", "tasks", "*.json"), recursive=True)

    for filepath in task_files:
        try:
            mtime = os.path.getmtime(filepath)
            if mtime < cutoff_ts:
                continue

            dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            agent_name = "Roo Code" if "roo" in filepath.lower() else "Cline"

            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "tokensIn" in item:
                        input_tok = item.get("tokensIn", 0)
                        output_tok = item.get("tokensOut", 0)
                        model = item.get("model", "claude-3-5-sonnet")
                        cost = calculate_cost(model, input_tok, output_tok)
                        events.append({
                            "timestamp": dt,
                            "agent": agent_name,
                            "model": model,
                            "input_tokens": input_tok,
                            "output_tokens": output_tok,
                            "cache_write_tokens": 0,
                            "cache_read_tokens": 0,
                            "total_tokens": input_tok + output_tok,
                            "cost": cost,
                        })
        except Exception as e:
            logger.debug("Error leyendo log de Roo/Cline %s: %s", filepath, e)

    return events
