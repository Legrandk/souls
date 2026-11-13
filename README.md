# Soulseek TUI

A small terminal client for connecting to Soulseek, searching shared files, queuing downloads, and watching download progress.

## Requirements

- macOS 10.15 Catalina or newer, or Linux, with Python 3.10+
- A Soulseek account
- Terminal with a UTF-8 capable terminal emulator

This is distributed as a Python package rather than a signed Mac installer. It does not require Developer ID. On Catalina, install a supported Python version from [python.org](https://www.python.org/downloads/macos/) first; the system Python is not suitable.

## Install and run

From the project folder, run:

```sh
./souls.sh
```

On first launch, the script creates a local virtual environment and installs the app and its dependencies. It requires Python 3.10 or newer. On Catalina, install a supported Python version from [python.org](https://www.python.org/downloads/macos/) first. Later launches reuse the environment.

To run the module directly from a source checkout instead:

```sh
python3 -m pip install --user .
python3 -m soulseek_tui
```

At first launch, enter your Soulseek username and password and choose a download folder. The username and folder are saved in the user config directory. The password is saved to the operating system keychain when available; if keychain storage is unavailable, it is requested on the next launch.

## Controls

- `/` — start a network search
- `c` — open configuration and edit the download directory
- Up/Down or `j`/`k` — select a result
- Enter or `d` — queue the selected file
- `q` — quit

Search results appear above the live downloads list. The downloads list shows transfer state, bytes, percent complete, speed, peer, and remote path.

The configuration screen currently saves the download directory and applies it to newly queued downloads immediately. Existing transfers keep their current destination.

Library warnings are written to `soulseek-tui.log` in the app configuration directory so they do not overwrite the terminal interface. On macOS, this is `~/Library/Application Support/soulseek-tui/soulseek-tui.log`.

## Tests

Run the standard-library unit tests with:

```sh
python3 -m unittest discover -s tests -v
```
