import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from soulseek_tui.app import _first_run_setup


class AppSetupTests(unittest.TestCase):
    def test_first_run_uses_requested_default_download_directory(self):
        with (
            patch("soulseek_tui.app.load_config", return_value={}),
            patch("soulseek_tui.app.get_password", return_value="secret"),
            patch("soulseek_tui.app.save_config") as save,
            patch("builtins.input", side_effect=["alice", ""]),
            patch("pathlib.Path.mkdir") as mkdir,
        ):
            username, password, download_dir = _first_run_setup()

        expected = Path.home() / "Downloads" / "souls"
        self.assertEqual((username, password, download_dir), ("alice", "secret", expected))
        mkdir.assert_called_once_with(parents=True, exist_ok=True)
        save.assert_called_once_with("alice", expected)

    def test_saved_account_starts_without_reentering_setup(self):
        with tempfile.TemporaryDirectory() as directory:
            saved = {"username": "alice", "download_dir": directory}
            with (
                patch("soulseek_tui.app.load_config", return_value=saved),
                patch("soulseek_tui.app.get_password", return_value="secret"),
                patch("soulseek_tui.app.save_config"),
                patch("builtins.input", side_effect=AssertionError("unexpected prompt")),
            ):
                username, password, download_dir = _first_run_setup()

        self.assertEqual(username, "alice")
        self.assertEqual(password, "secret")
        self.assertEqual(download_dir, Path(directory))


if __name__ == "__main__":
    unittest.main()
