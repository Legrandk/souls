"""Adapter between the UI and the aioslsk Soulseek client."""

from pathlib import Path

from .models import search_hits, transfer_view


class SoulseekBackend:
    def __init__(self, username: str, password: str, download_dir: Path):
        self.username = username
        self.password = password
        self.download_dir = download_dir
        self.client = None

    async def start(self) -> None:
        from aioslsk.client import SoulSeekClient
        from aioslsk.settings import CredentialsSettings, Settings, SharesSettings

        settings = Settings(
            credentials=CredentialsSettings(username=self.username, password=self.password),
            shares=SharesSettings(scan_on_start=False, download=str(self.download_dir)),
        )
        self.client = SoulSeekClient(settings)
        await self.client.start()
        await self.client.login()

    async def close(self) -> None:
        if self.client is not None:
            await self.client.stop()
            self.client = None

    async def search(self, query: str):
        return await self.client.searches.search(query)

    async def read_search(self, request):
        return search_hits(request.results)

    async def download(self, hit) -> None:
        await self.client.transfers.download(hit.username, hit.filename)

    async def downloads(self):
        return [transfer_view(item) for item in self.client.transfers.get_downloads()]

    async def set_download_dir(self, directory: Path) -> None:
        if not str(directory).strip():
            raise ValueError("Download directory cannot be empty")
        self.download_dir = Path(directory).expanduser()
        self.download_dir.mkdir(parents=True, exist_ok=True)
        if self.client is not None:
            self.client.settings.shares.download = str(self.download_dir)
