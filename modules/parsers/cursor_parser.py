"""Parser de consumo para Cursor IDE (SQLite & state storage)."""
import glob
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone

from config.config import CURSOR_STORAGE_DIR
from modules.pricing import calculate_cost

logger = logging.getLogger(__name__)


def parse_cursor_logs(max_days: int = 90) -> list:
    """Extrae eventos de consumo de las bases de datos state.vscdb en Cursor storage."""
    events = []
    if not os.path.exists(CURSOR_STORAGE_DIR):
        return events

    cutoff_ts = datetime.now(timezone.utc).timestamp() - (max_days * 86400)
    db_files = glob.glob(os.path.join(CURSOR_STORAGE_DIR, "**", "state.vscdb"), recursive=True)

    for db_path in db_files:
        try:
            if os.path.getmtime(db_path) < cutoff_ts:
                continue

            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%ai%' OR key LIKE '%token%' OR key LIKE '%chat%'")
            rows = cursor.fetchall()
            conn.close()

            for key, val in rows:
                if not val:
                    continue
                try:
                    data = json.loads(val)
                    if isinstance(data, dict) and ("token" in str(data).lower() or "model" in str(data).lower()):
                        model = data.get("modelName", data.get("model", "gpt-4o"))
                        input_tok = data.get("promptTokens", data.get("inputTokens", 200))
                        output_tok = data.get("completionTokens", data.get("outputTokens", 100))
                        cost = calculate_cost(model, input_tok, output_tok)
                        dt = datetime.fromtimestamp(os.path.getmtime(db_path), tz=timezone.utc)
                        events.append({
                            "timestamp": dt,
                            "agent": "Cursor",
                            "model": model,
                            "input_tokens": input_tok,
                            "output_tokens": output_tok,
                            "cache_write_tokens": 0,
                            "cache_read_tokens": 0,
                            "total_tokens": input_tok + output_tok,
                            "cost": cost,
                        })
                except Exception:
                    continue
        except Exception as e:
            logger.debug("Error procesando DB de Cursor %s: %s", db_path, e)

    return events
