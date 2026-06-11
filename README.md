# Token Dashboard

Quota restante de **Claude Code** y **Antigravity** en la barra superior de GNOME:
porcentaje de la sesión junto al icono, detalle y horas de reset en el menú,
y ventana GTK con barras de progreso.

## Fuentes de datos

- **Claude Code**: endpoint OAuth `api.anthropic.com/api/oauth/usage` con la
  credencial local de `~/.claude/.credentials.json` (lo mismo que `/usage`).
- **Antigravity**: CLI `antigravity-usage quota --json`.

## Requisitos

```bash
sudo apt install gir1.2-ayatanaappindicator3-0.1
```

(PyGObject/GTK3 ya vienen con Ubuntu; `antigravity-usage` debe estar en el PATH.)

## Uso

```bash
python3 main.py
```

## Autostart

```bash
cp token-dashboard.desktop ~/.config/autostart/
```

## Configuración (env vars)

| Variable | Default |
|---|---|
| `REFRESH_INTERVAL_MINUTES` | `5` |
| `CLAUDE_CREDENTIALS_PATH` | `~/.claude/.credentials.json` |
| `ANTIGRAVITY_USAGE_BIN` | `antigravity-usage` |
