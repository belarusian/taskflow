"""Configuration management utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml


DEFAULT_CONFIG = {
    "storage_dir": "~/.taskflow",
    "server": {
        "host": "127.0.0.1",
        "port": 8765,
        "ws_path": "/ws",
    },
    "notifications": {
        "enabled": True,
        "max_history": 1000,
    },
    "ui": {
        "color": True,
        "compact": False,
    },
}


def get_config_path() -> Path:
    """Get the path to the config file."""
    config_dir = Path.home() / ".taskflow"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.yaml"


def load_config() -> dict:
    """Load configuration from file, merging with defaults."""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f) or {}
        # Deep merge with defaults
        config = _deep_merge(DEFAULT_CONFIG, user_config)
    else:
        config = DEFAULT_CONFIG.copy()
        # Write initial config
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    return config


def save_config(config: dict) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_config(key: Optional[str] = None) -> Any:
    """Get a config value by key path (dot notation)."""
    config = load_config()
    if key is None:
        return config
    parts = key.split(".")
    value = config
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def set_config(key: str, value: Any) -> None:
    """Set a config value by key path (dot notation)."""
    config = load_config()
    parts = key.split(".")
    target = config
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]
    target[parts[-1]] = value
    save_config(config)


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
