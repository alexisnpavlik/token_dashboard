"""Configuración del dashboard de quota via variables de entorno."""
import os

CLAUDE_CREDENTIALS_PATH = os.getenv(
    "CLAUDE_CREDENTIALS_PATH", os.path.expanduser("~/.claude/.credentials.json")
)
CLAUDE_LOGS_DIR = os.getenv(
    "CLAUDE_LOGS_DIR", os.path.expanduser("~/.claude")
)
CLAUDE_USAGE_URL = os.getenv(
    "CLAUDE_USAGE_URL", "https://api.anthropic.com/api/oauth/usage"
)

ANTIGRAVITY_USAGE_BIN = os.getenv("ANTIGRAVITY_USAGE_BIN", "antigravity-usage")
ANTIGRAVITY_LOGS_DIR = os.getenv(
    "ANTIGRAVITY_LOGS_DIR", os.path.expanduser("~/.gemini")
)

CURSOR_STORAGE_DIR = os.getenv(
    "CURSOR_STORAGE_DIR", os.path.expanduser("~/.config/Cursor/User")
)
AIDER_LOGS_DIR = os.getenv(
    "AIDER_LOGS_DIR", os.path.expanduser("~")
)
ROO_CLINE_LOGS_DIR = os.getenv(
    "ROO_CLINE_LOGS_DIR", os.path.expanduser("~/.config/Code/User/globalStorage")
)

SETTINGS_FILE = os.getenv(
    "TOKENBAR_SETTINGS_FILE", os.path.expanduser("~/.config/token_dashboard/settings.json")
)

REFRESH_INTERVAL_MINUTES = int(os.getenv("REFRESH_INTERVAL_MINUTES", "5"))

