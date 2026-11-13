"""Application entry point and first-run setup."""

import asyncio
import getpass
import sys
from pathlib import Path

from .backend import SoulseekBackend
from .config import configure_logging, get_password, load_config, save_config, set_password
from .ui import run_ui


def _first_run_setup() -> tuple[str, str, Path]:
    saved = load_config()
    username = saved.get("username", "")
    if not username:
        username = input("Soulseek username: ").strip()
    if not username:
        raise ValueError("A Soulseek username is required")

    download_dir = saved.get("download_dir")
    if download_dir:
        download_dir = Path(download_dir).expanduser()
    else:
        download_default = Path.home() / "Downloads" / "souls"
        download_text = input(f"Download folder [{download_default}]: ").strip()
        download_dir = Path(download_text or download_default).expanduser()
    download_dir.mkdir(parents=True, exist_ok=True)

    try:
        password = get_password(username)
    except Exception:
        password = None
    if not password:
        password = getpass.getpass("Soulseek password: ")
        try:
            set_password(username, password)
        except Exception:
            print("Could not save password to the system keychain; it will be requested next time.")
    save_config(username, download_dir)
    return username, password, download_dir


async def _run() -> None:
    username, password, download_dir = _first_run_setup()
    configure_logging()
    backend = SoulseekBackend(username, password, download_dir)
    await run_ui(backend)


def main() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit("Soulseek TUI requires Python 3.10 or newer")
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        raise SystemExit(f"Soulseek TUI: {exc}") from exc


if __name__ == "__main__":
    main()
