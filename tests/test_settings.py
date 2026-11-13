import unittest
from pathlib import Path
from unittest.mock import patch

from soulseek_tui.ui import _save_credentials, _save_download_dir


class SettingsTests(unittest.IsolatedAsyncioTestCase):
    async def test_account_change_saves_password_and_reconnects(self):
        class Backend:
            username = "old-user"
            download_dir = Path("/tmp/downloads")

            async def set_credentials(self, username, password):
                self.credentials = (username, password)

        backend = Backend()
        with (
            patch("soulseek_tui.ui.save_config") as save,
            patch("soulseek_tui.ui.set_password") as set_secret,
        ):
            result = await _save_credentials(backend, "new-user", "new-pass")

        self.assertEqual(result, ("new-user", True))
        self.assertEqual(backend.credentials, ("new-user", "new-pass"))
        save.assert_called_once_with("new-user", backend.download_dir)
        set_secret.assert_called_once_with("new-user", "new-pass")

    async def test_account_change_requires_a_password_when_none_is_saved(self):
        class Backend:
            username = "user"
            download_dir = Path("/tmp/downloads")

            async def set_credentials(self, username, password):
                self.credentials = (username, password)

        with (
            patch("soulseek_tui.ui.get_password", return_value=None),
            patch("soulseek_tui.ui.save_config"),
        ):
            with self.assertRaisesRegex(ValueError, "Enter a password"):
                await _save_credentials(Backend(), "new-user", "")

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
