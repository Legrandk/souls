import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from soulseek_tui import config


class ConfigTests(unittest.TestCase):
    def test_library_warnings_go_to_rotating_log_file(self):
        logger = logging.getLogger("aioslsk")
        old_handlers = logger.handlers[:]
        old_level = logger.level
        old_propagate = logger.propagate
        logger.handlers = []
        try:
            with tempfile.TemporaryDirectory() as directory:
                config_file = Path(directory) / "config.json"
                with patch("soulseek_tui.config.config_path", return_value=config_file):
                    log_path = config.configure_logging()
                logger.warning("expected peer disconnect")
                logger.handlers[0].flush()
                self.assertEqual(log_path, Path(directory) / "soulseek-tui.log")
                self.assertIn("expected peer disconnect", log_path.read_text())
                self.assertFalse(logger.propagate)
        finally:
            for handler in logger.handlers:
                handler.close()
            logger.handlers = old_handlers
            logger.setLevel(old_level)
            logger.propagate = old_propagate

    def test_preferences_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            with patch("soulseek_tui.config.config_path", return_value=path):
                config.save_config("alice", Path(directory) / "Music")
                self.assertEqual(
                    config.load_config(),
                    {"username": "alice", "download_dir": str(Path(directory) / "Music")},
                )
            self.assertEqual(json.loads(path.read_text()), {
                "username": "alice",
                "download_dir": str(Path(directory) / "Music"),
            })

    def test_missing_or_invalid_config_returns_empty_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.json"
            with patch("soulseek_tui.config.config_path", return_value=path):
                self.assertEqual(config.load_config(), {})
                path.write_text("not json")
                self.assertEqual(config.load_config(), {})


if __name__ == "__main__":
    unittest.main()
