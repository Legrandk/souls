import unittest
from types import SimpleNamespace

from soulseek_tui.models import (
    SearchHit,
    TransferView,
    format_size,
    format_transfer,
    search_hits,
    transfer_view,
)


class ModelsTests(unittest.TestCase):
    def test_search_results_become_downloadable_hits(self):
        results = [
            SimpleNamespace(
                username="alice",
                shared_items=[
                    SimpleNamespace(filename="album/track.flac", filesize=1024),
                    SimpleNamespace(filename="album/cover.jpg", filesize=512),
                ],
            )
        ]

        self.assertEqual(
            search_hits(results),
            [
                SearchHit("alice", "album/track.flac", 1024),
                SearchHit("alice", "album/cover.jpg", 512),
            ],
        )

    def test_transfer_view_includes_progress_and_status(self):
        transfer = SimpleNamespace(
            username="alice",
            remote_path="album/track.flac",
            filesize=2048,
            progress_snapshot=SimpleNamespace(
                state=SimpleNamespace(name="DOWNLOADING"),
                bytes_transfered=1024,
                speed=512.0,
            ),
        )

        self.assertEqual(
            transfer_view(transfer),
            TransferView("alice", "album/track.flac", "DOWNLOADING", 1024, 2048, 512.0),
        )
        line = format_transfer(transfer_view(transfer))
        self.assertIn("DOWNLOADING", line)
        self.assertIn("50%", line)
        self.assertIn("alice: album/track.flac", line)

    def test_size_formatting_handles_missing_and_large_sizes(self):
        self.assertEqual(format_size(None), "?")
        self.assertEqual(format_size(64), "64 B")
        self.assertEqual(format_size(1536), "1.5 KB")


if __name__ == "__main__":
    unittest.main()
