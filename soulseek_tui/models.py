"""Small display models and formatting helpers for the terminal UI."""

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SearchHit:
    username: str
    filename: str
    filesize: int


@dataclass(frozen=True)
class TransferView:
    username: str
    filename: str
    state: str
    transferred: int
    filesize: int | None
    speed: float


def format_size(size: int | None) -> str:
    if size is None:
        return "?"
    amount = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
    return "?"


def search_hits(results: Iterable[object]) -> list[SearchHit]:
    hits = []
    for result in results:
        username = result.username
        for item in result.shared_items:
            hits.append(SearchHit(username, item.filename, item.filesize))
    return hits


def transfer_view(transfer: object) -> TransferView:
    snapshot = transfer.progress_snapshot
    state = snapshot.state
    state_name = getattr(state, "name", str(state)).replace("TransferState.", "")
    return TransferView(
        username=transfer.username,
        filename=transfer.remote_path,
        state=state_name,
        transferred=snapshot.bytes_transfered,
        filesize=transfer.filesize,
        speed=snapshot.speed,
    )


def format_transfer(transfer: TransferView) -> str:
    size = format_size(transfer.filesize)
    progress = format_size(transfer.transferred)
    percent = ""
    if transfer.filesize:
        percent = f" {min(100, int(100 * transfer.transferred / transfer.filesize))}%"
    speed = f" {format_size(int(transfer.speed))}/s" if transfer.speed > 0 else ""
    return f"{transfer.state:<12} {progress}/{size}{percent}{speed}  {transfer.username}: {transfer.filename}"
