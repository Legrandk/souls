"""User preferences and Keychain-backed credential storage."""

import json
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

SERVICE_NAME = "soulseek-tui"


def config_path() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif os.environ.get("XDG_CONFIG_HOME"):
        base = Path(os.environ["XDG_CONFIG_HOME"])
    else:
        base = Path.home() / ".config"
    return base / SERVICE_NAME / "config.json"


def load_config() -> dict:
    try:
        return json.loads(config_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(username: str, download_dir: Path) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"username": username, "download_dir": str(download_dir)}, indent=2),
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    temporary.replace(path)


def get_password(username: str) -> str | None:
    import keyring

    return keyring.get_password(SERVICE_NAME, username)


def set_password(username: str, password: str) -> None:
    import keyring

    keyring.set_password(SERVICE_NAME, username, password)


def configure_logging() -> Path:
    log_path = config_path().parent / "soulseek-tui.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("aioslsk")
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    logger.propagate = False
    return log_path
