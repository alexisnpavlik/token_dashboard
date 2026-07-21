"""Tabla de precios y calculadora de costo estimado ($ USD) para modelos de IA."""

# Precios expresados por cada 1,000,000 (1M) de tokens en USD
MODEL_PRICING = {
    # Anthropic Claude
    "claude-3-7-sonnet": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00, "cache_write": 1.00, "cache_read": 0.08},
    "claude-3-opus": {"input": 15.00, "output": 75.00, "cache_write": 18.75, "cache_read": 1.50},
    "claude-opus-4": {"input": 15.00, "output": 75.00, "cache_write": 18.75, "cache_read": 1.50},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30},

    # Google Gemini / Antigravity
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60, "cache_read": 0.0375},
    "gemini-3.5-flash": {"input": 0.15, "output": 0.60, "cache_read": 0.0375},
    "gemini-3.6-flash": {"input": 0.15, "output": 0.60, "cache_read": 0.0375},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00, "cache_read": 0.3125},
    "gemini-3.1-pro": {"input": 1.25, "output": 5.00, "cache_read": 0.3125},

    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00, "cache_read": 1.25},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "cache_read": 0.075},
    "o3-mini": {"input": 1.10, "output": 4.40, "cache_read": 0.55},
}

DEFAULT_PRICING = {"input": 2.00, "output": 8.00, "cache_write": 2.50, "cache_read": 0.20}


def get_model_pricing(model_name: str) -> dict:
    """Retorna las tarifas del modelo buscando por coincidencia parcial de nombre."""
    if not model_name:
        return DEFAULT_PRICING
    
    name_lower = model_name.lower().replace(" ", "-").replace("_", "-")
    for key, rates in MODEL_PRICING.items():
        if key in name_lower or name_lower in key:
            return rates
    
    # Heurísticas por proveedor/familia
    if "opus" in name_lower:
        return MODEL_PRICING["claude-3-opus"]
    if "sonnet" in name_lower:
        return MODEL_PRICING["claude-3-5-sonnet"]
    if "haiku" in name_lower:
        return MODEL_PRICING["claude-3-5-haiku"]
    if "flash" in name_lower:
        return MODEL_PRICING["gemini-2.5-flash"]
    if "pro" in name_lower:
        return MODEL_PRICING["gemini-2.5-pro"]
    if "gpt-4" in name_lower or "gpt4" in name_lower:
        return MODEL_PRICING["gpt-4o"]
        
    return DEFAULT_PRICING


def calculate_cost(
    model_name: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_write_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> float:
    """Calcula el costo estimado en dólares ($ USD) para un consumo dado."""
    rates = get_model_pricing(model_name)
    
    cost = 0.0
    cost += (input_tokens / 1_000_000.0) * rates.get("input", 0.0)
    cost += (output_tokens / 1_000_000.0) * rates.get("output", 0.0)
    cost += (cache_write_tokens / 1_000_000.0) * rates.get("cache_write", rates.get("input", 0.0))
    cost += (cache_read_tokens / 1_000_000.0) * rates.get("cache_read", rates.get("input", 0.0) * 0.1)
    
    return round(cost, 6)
