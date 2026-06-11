"""Configuración del dashboard de quota via variables de entorno."""
import os

CLAUDE_CREDENTIALS_PATH = os.getenv(
    "CLAUDE_CREDENTIALS_PATH", os.path.expanduser("~/.claude/.credentials.json")
)
CLAUDE_USAGE_URL = os.getenv(
    "CLAUDE_USAGE_URL", "https://api.anthropic.com/api/oauth/usage"
)
ANTIGRAVITY_USAGE_BIN = os.getenv("ANTIGRAVITY_USAGE_BIN", "antigravity-usage")
REFRESH_INTERVAL_MINUTES = int(os.getenv("REFRESH_INTERVAL_MINUTES", "5"))
