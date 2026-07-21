"""Motor de agregación multi-agente para métricas, matriz de contribución y cuotas."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from modules.parsers import (
    get_antigravity_quota,
    get_claude_quota,
    parse_aider_logs,
    parse_antigravity_logs,
    parse_claude_logs,
    parse_cursor_logs,
    parse_roo_cline_logs,
)


_aggregator_cache = {"data": None, "timestamp": 0}


def get_aggregated_data(max_days: int = 90) -> dict:
    """Consolida todas las métricas de consumo de los diferentes agentes de IA (cached 3s)."""
    now_ts = datetime.now(timezone.utc).timestamp()
    if _aggregator_cache["data"] and (now_ts - _aggregator_cache["timestamp"]) < 3:
        return _aggregator_cache["data"]

    # Colectar eventos de todos los parsers

    all_events = []
    all_events.extend(parse_claude_logs(max_days))
    all_events.extend(parse_antigravity_logs(max_days))
    all_events.extend(parse_cursor_logs(max_days))
    all_events.extend(parse_aider_logs(max_days))
    all_events.extend(parse_roo_cline_logs(max_days))

    now = datetime.now(timezone.utc)
    today_date = now.date()
    seven_days_ago = now - timedelta(days=7)
    fifteen_mins_ago = now - timedelta(minutes=15)

    today_tokens = 0
    today_cost = 0.0

    seven_day_tokens = 0
    seven_day_cost = 0.0

    total_tokens = 0
    total_cost = 0.0

    recent_15m_tokens = 0

    heatmap_days = defaultdict(lambda: {"tokens": 0, "cost": 0.0})
    models_usage = defaultdict(lambda: {"tokens": 0, "cost": 0.0})
    agents_usage = defaultdict(lambda: {"tokens": 0, "cost": 0.0})

    hourly_dist = [0] * 24
    daily_dist = [0] * 7  # 0=Lunes, 6=Domingo

    for event in all_events:
        ts = event["timestamp"]
        ev_date = ts.date()
        ev_date_str = ev_date.isoformat()
        tok = event["total_tokens"]
        cost = event["cost"]
        model = event["model"]
        agent = event["agent"]

        # Totales globales
        total_tokens += tok
        total_cost += cost

        # Heatmap diario
        heatmap_days[ev_date_str]["tokens"] += tok
        heatmap_days[ev_date_str]["cost"] += cost

        # Desglose por modelo y agente
        models_usage[model]["tokens"] += tok
        models_usage[model]["cost"] += cost

        agents_usage[agent]["tokens"] += tok
        agents_usage[agent]["cost"] += cost

        # Hoy
        if ev_date == today_date:
            today_tokens += tok
            today_cost += cost

        # 7 días
        if ts >= seven_days_ago:
            seven_day_tokens += tok
            seven_day_cost += cost

        # Velocidad en los últimos 15 min
        if ts >= fifteen_mins_ago:
            recent_15m_tokens += tok

        # Distribución horaria y diaria
        hourly_dist[ts.hour] += tok
        daily_dist[ts.weekday()] += tok

    # Tokens por minuto (velocidad actual)
    tokens_per_min = round(recent_15m_tokens / 15.0, 1)

    # Formatear matriz de contribución (heatmap 90 días)
    heatmap_matrix = []
    max_daily_tokens = max((v["tokens"] for v in heatmap_days.values()), default=1) or 1

    for d in range(max_days - 1, -1, -1):
        day_dt = (today_date - timedelta(days=d))
        day_str = day_dt.isoformat()
        day_info = heatmap_days.get(day_str, {"tokens": 0, "cost": 0.0})
        tok_val = day_info["tokens"]

        # Intensidad de 0 a 4 (estilo GitHub)
        if tok_val == 0:
            intensity = 0
        elif tok_val < (max_daily_tokens * 0.25):
            intensity = 1
        elif tok_val < (max_daily_tokens * 0.50):
            intensity = 2
        elif tok_val < (max_daily_tokens * 0.75):
            intensity = 3
        else:
            intensity = 4

        heatmap_matrix.append({
            "date": day_str,
            "weekday": day_dt.weekday(),
            "tokens": tok_val,
            "cost": round(day_info["cost"], 4),
            "intensity": intensity,
        })

    # Formatear desglose por modelos (ordenado por tokens)
    models_list = []
    for mod, data in sorted(models_usage.items(), key=lambda x: x[1]["tokens"], reverse=True):
        pct = (data["tokens"] / total_tokens * 100.0) if total_tokens > 0 else 0.0
        models_list.append({
            "model": mod,
            "tokens": data["tokens"],
            "cost": round(data["cost"], 4),
            "percentage": round(pct, 1),
        })

    # Formatear desglose por agentes (ordenado por tokens)
    agents_list = []
    for ag, data in sorted(agents_usage.items(), key=lambda x: x[1]["tokens"], reverse=True):
        pct = (data["tokens"] / total_tokens * 100.0) if total_tokens > 0 else 0.0
        agents_list.append({
            "agent": ag,
            "tokens": data["tokens"],
            "cost": round(data["cost"], 4),
            "percentage": round(pct, 1),
        })

    # Consultar cuotas actuales
    claude_quota = get_claude_quota()
    antigravity_quota = get_antigravity_quota()

    result = {
        "today_tokens": today_tokens,
        "today_cost": round(today_cost, 4),
        "seven_day_tokens": seven_day_tokens,
        "seven_day_cost": round(seven_day_cost, 4),
        "total_tokens": total_tokens,
        "total_cost": round(total_cost, 4),
        "tokens_per_min": tokens_per_min,
        "heatmap": heatmap_matrix,
        "models": models_list,
        "agents": agents_list,
        "hourly_distribution": hourly_dist,
        "daily_distribution": daily_dist,
        "claude_quota": claude_quota,
        "antigravity_quota": antigravity_quota,
        "updated_at": now,
    }
    _aggregator_cache["data"] = result
    _aggregator_cache["timestamp"] = now_ts
    return result

