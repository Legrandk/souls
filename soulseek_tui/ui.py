"""A compact curses interface for searching and tracking downloads."""

import asyncio
import curses
import time
from concurrent.futures import Future
from pathlib import Path

from .config import save_config
from .models import SearchHit, TransferView, format_size, format_transfer


def _write(window, y: int, x: int, text: str, width: int, attr: int = 0) -> None:
    height, screen_width = window.getmaxyx()
    if y < height and x < screen_width - 1:
        try:
            window.addnstr(y, x, text, min(width, screen_width - x - 1), attr)
        except curses.error:
            pass


def _draw(
    window,
    status: str,
    query: str,
    input_mode: bool,
    hits: list[SearchHit],
    selected: int,
    transfers: list[TransferView],
    scroll: int,
) -> None:
    window.erase()
    height, width = window.getmaxyx()
    _write(window, 0, 0, f"Soulseek TUI  |  {status}", width, curses.A_BOLD)
    prompt = f"Search: {query}{'_' if input_mode else ''}" if input_mode else "/ search   ↑/↓ select   Enter download   c config   q quit"
    _write(window, 1, 0, prompt, width)
    _write(window, 3, 0, f"SEARCH RESULTS ({len(hits)})", width, curses.A_BOLD)

    transfer_heading = max(5, height - min(8, len(transfers) + 2) - 1)
    result_capacity = max(0, transfer_heading - 4)
    for index, hit in enumerate(hits[scroll : scroll + result_capacity]):
        absolute_index = scroll + index
        prefix = "> " if absolute_index == selected else "  "
        line = f"{prefix}{hit.username:<18} {format_size(hit.filesize):>9}  {hit.filename}"
        _write(window, 4 + index, 0, line, width, curses.A_REVERSE if absolute_index == selected else 0)

    _write(window, transfer_heading, 0, f"DOWNLOADS ({len(transfers)})", width, curses.A_BOLD)
    max_transfers = min(5, height - transfer_heading - 2)
    if not transfers:
        _write(window, transfer_heading + 1, 0, "No downloads yet", width)
    for index, transfer in enumerate(transfers[:max_transfers]):
        _write(window, transfer_heading + 1 + index, 0, format_transfer(transfer), width)
    window.refresh()


def _draw_settings(window, status: str, download_dir: str, editing: bool, value: str) -> None:
    window.erase()
    _, width = window.getmaxyx()
    _write(window, 0, 0, f"Configuration  |  {status}", width, curses.A_BOLD)
    _write(window, 2, 0, "Download directory", width, curses.A_BOLD)
    _write(window, 3, 2, value if editing else download_dir, width - 2)
    if editing:
        _write(window, 5, 0, "Type a folder path, Enter to save, Esc to cancel", width)
    else:
        _write(window, 5, 0, "Enter/e edit   Esc return", width)
        _write(window, 7, 0, "New settings can be added to this screen.", width)
    window.refresh()


async def _save_download_dir(backend, value: str) -> Path:
    if not value.strip():
        raise ValueError("Download directory cannot be empty")
    path = Path(value).expanduser()
    await backend.set_download_dir(path)
    save_config(backend.username, path)
    return path


def run_curses(window, backend, loop: asyncio.AbstractEventLoop) -> None:
    curses.curs_set(0)
    window.nodelay(True)
    status = "Connecting"
    query = ""
    input_mode = False
    hits: list[SearchHit] = []
    transfers: list[TransferView] = []
    selected = 0
    scroll = 0
    request = None
    search_future: Future | None = None
    read_future: Future | None = None
    transfer_future: Future | None = None
    download_future: Future | None = None
    transfer_refresh_at = 0.0
    read_refresh_at = 0.0
    stopping = False
    connected = False
    screen = "main"
    settings_editing = False
    settings_value = str(backend.download_dir)
    settings_future: Future | None = None

    start_future = asyncio.run_coroutine_threadsafe(backend.start(), loop)
    while not stopping:
        now = time.monotonic()
        if start_future is not None and start_future.done():
            try:
                start_future.result()
                status = "Connected"
                connected = True
            except Exception as exc:
                status = f"Connection failed: {exc}"
            start_future = None
        if search_future is not None and search_future.done():
            try:
                request = search_future.result()
                hits = []
                status = f"Searching: {query}"
                read_refresh_at = 0
            except Exception as exc:
                status = f"Search failed: {exc}"
            search_future = None
        if request is not None and read_future is None and now >= read_refresh_at:
            read_future = asyncio.run_coroutine_threadsafe(backend.read_search(request), loop)
            read_refresh_at = now + 0.5
        if read_future is not None and read_future.done():
            try:
                hits = read_future.result()
                if hits:
                    status = f"{len(hits)} results"
                elif status.startswith("Searching:"):
                    status = f"Searching: {query} (no results yet)"
                selected = min(selected, max(0, len(hits) - 1))
                scroll = min(scroll, selected)
            except Exception as exc:
                status = f"Could not read results: {exc}"
            read_future = None
        if connected and transfer_future is None and now >= transfer_refresh_at:
            transfer_future = asyncio.run_coroutine_threadsafe(backend.downloads(), loop)
            transfer_refresh_at = now + 0.5
        if transfer_future is not None and transfer_future.done():
            try:
                transfers = transfer_future.result()
            except Exception as exc:
                status = f"Transfer update failed: {exc}"
            transfer_future = None
        if download_future is not None and download_future.done():
            try:
                download_future.result()
            except Exception as exc:
                status = f"Download failed: {exc}"
            download_future = None
        if settings_future is not None and settings_future.done():
            try:
                backend.download_dir = settings_future.result()
                settings_value = str(backend.download_dir)
                status = "Download directory saved"
            except Exception as exc:
                status = f"Could not save setting: {exc}"
            settings_future = None

        if screen == "settings":
            _draw_settings(window, status, str(backend.download_dir), settings_editing, settings_value)
        else:
            _draw(window, status, query, input_mode, hits, selected, transfers, scroll)
        try:
            raw_key = window.get_wch()
            key = ord(raw_key) if isinstance(raw_key, str) else raw_key
        except curses.error:
            key = -1
        if key == -1:
            time.sleep(0.05)
            continue
        if screen == "settings" and settings_editing:
            if key in (10, 13):
                if settings_value.strip():
                    settings_future = asyncio.run_coroutine_threadsafe(
                        _save_download_dir(backend, settings_value.strip()), loop
                    )
                    status = "Saving download directory..."
                    settings_editing = False
                else:
                    status = "Download directory cannot be empty"
            elif key == 27:
                settings_editing = False
                settings_value = str(backend.download_dir)
            elif key in (curses.KEY_BACKSPACE, 8, 127):
                settings_value = settings_value[:-1]
            elif 32 <= key <= 0x10FFFF and chr(key).isprintable() and len(settings_value) < 500:
                settings_value += chr(key)
            continue

        if input_mode:
            if key in (10, 13):
                term = query.strip()
                input_mode = False
                if term:
                    query = term
                    hits = []
                    selected = scroll = 0
                    request = None
                    read_future = None
                    status = f"Searching: {query}"
                    search_future = asyncio.run_coroutine_threadsafe(backend.search(query), loop)
            elif key == 27:
                input_mode = False
                query = ""
            elif key in (curses.KEY_BACKSPACE, 8, 127):
                query = query[:-1]
            elif 32 <= key <= 0x10FFFF and chr(key).isprintable() and len(query) < 200:
                query += chr(key)
            continue

        if key in (ord("q"), ord("Q")):
            stopping = True
        elif screen == "settings" and key == 27:
            screen = "main"
            status = "Connected" if connected else status
        elif screen == "settings" and key in (10, 13, ord("e"), ord("E")) and settings_future is None:
            settings_editing = True
            settings_value = str(backend.download_dir)
        elif key == ord("/"):
            if screen == "main" and connected and search_future is None:
                input_mode = True
                query = ""
        elif screen == "main" and key in (ord("c"), ord("C")):
            screen = "settings"
        elif screen == "main" and key in (curses.KEY_UP, ord("k")):
            selected = max(0, selected - 1)
            if selected < scroll:
                scroll = selected
        elif screen == "main" and key in (curses.KEY_DOWN, ord("j")):
            selected = min(max(0, len(hits) - 1), selected + 1)
            transfer_heading = max(5, window.getmaxyx()[0] - min(8, len(transfers) + 2) - 1)
            capacity = max(1, transfer_heading - 4)
            if selected >= scroll + capacity:
                scroll = selected - capacity + 1
        elif screen == "main" and key in (10, 13, ord("d"), ord("D")) and hits and search_future is None:
            hit = hits[selected]
            download_future = asyncio.run_coroutine_threadsafe(backend.download(hit), loop)
            status = f"Queued: {hit.filename}"

    try:
        curses.curs_set(1)
    except curses.error:
        pass
    shutdown = asyncio.run_coroutine_threadsafe(backend.close(), loop)
    try:
        shutdown.result(timeout=5)
    except Exception:
        pass


async def run_ui(backend) -> None:
    loop = asyncio.get_running_loop()
    await asyncio.to_thread(curses.wrapper, run_curses, backend, loop)
