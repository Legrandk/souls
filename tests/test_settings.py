import unittest
from pathlib import Path
from unittest.mock import patch

from soulseek_tui.ui import _save_download_dir


class SettingsTests(unittest.IsolatedAsyncioTestCase):
    async def test_download_directory_is_applied_and_persisted(self):
        class Backend:
            username = "alice"

            async def set_download_dir(self, directory):
                self.directory = directory

        backend = Backend()
        expected = Path.home() / "Music" / "Soulseek"
        with patch("soulseek_tui.ui.save_config") as save:
            actual = await _save_download_dir(backend, "~/Music/Soulseek")

        self.assertEqual(actual, expected)
        self.assertEqual(backend.directory, expected)
        save.assert_called_once_with("alice", expected)

    async def test_empty_download_directory_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            await _save_download_dir(object(), "  ")


if __name__ == "__main__":
    unittest.main()
