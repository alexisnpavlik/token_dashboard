"""Paquete de parsers de consumo de logs para diversos agentes de IA."""
from modules.parsers.aider_parser import parse_aider_logs
from modules.parsers.antigravity_parser import get_antigravity_quota, parse_antigravity_logs
from modules.parsers.claude_parser import get_claude_quota, parse_claude_logs
from modules.parsers.cursor_parser import parse_cursor_logs
from modules.parsers.roo_cline_parser import parse_roo_cline_logs

__all__ = [
    "get_claude_quota",
    "parse_claude_logs",
    "get_antigravity_quota",
    "parse_antigravity_logs",
    "parse_cursor_logs",
    "parse_aider_logs",
    "parse_roo_cline_logs",
]
