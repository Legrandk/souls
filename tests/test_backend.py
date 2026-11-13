import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from soulseek_tui.backend import SoulseekBackend
from soulseek_tui.models import SearchHit, TransferView


class BackendTests(unittest.IsolatedAsyncioTestCase):
    async def test_download_directory_updates_current_client_and_creates_folder(self):
        with patch("pathlib.Path.mkdir") as mkdir:
            backend = SoulseekBackend("self", "secret", Path("/tmp/old"))
            backend.client = SimpleNamespace(
                settings=SimpleNamespace(shares=SimpleNamespace(download="/tmp/old"))
            )

            await backend.set_download_dir(Path("/tmp/new"))

        self.assertEqual(backend.download_dir, Path("/tmp/new"))
        self.assertEqual(backend.client.settings.shares.download, "/tmp/new")
        mkdir.assert_called_once_with(parents=True, exist_ok=True)

    async def test_search_download_and_transfer_snapshot(self):
        request = SimpleNamespace(
            results=[
                SimpleNamespace(
                    username="alice",
                    shared_items=[SimpleNamespace(filename="song.flac", filesize=500)],
                )
            ]
        )
        transfer = SimpleNamespace(
            username="alice",
            remote_path="song.flac",
            filesize=500,
            progress_snapshot=SimpleNamespace(
                state="QUEUED", bytes_transfered=0, speed=0,
            ),
        )
        downloaded = []

        class SearchManager:
            async def search(self, query):
                self.query = query
                return request

        class TransferManager:
            async def download(self, username, filename):
                downloaded.append((username, filename))

            def get_downloads(self):
                return [transfer]

        backend = SoulseekBackend("self", "secret", Path("/tmp/downloads"))
        backend.client = SimpleNamespace(searches=SearchManager(), transfers=TransferManager())

        found = await backend.search("song")
        self.assertIs(found, request)
        self.assertEqual(backend.client.searches.query, "song")
        self.assertEqual(await backend.read_search(found), [SearchHit("alice", "song.flac", 500)])

        await backend.download(SearchHit("alice", "song.flac", 500))
        self.assertEqual(downloaded, [("alice", "song.flac")])
        self.assertEqual(
            await backend.downloads(),
            [TransferView("alice", "song.flac", "QUEUED", 0, 500, 0)],
        )


if __name__ == "__main__":
    unittest.main()
