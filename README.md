# ACS ACR1252U USB NFC Reader - TUI & CLI (Ubuntu Linux)

[![Reader](https://img.shields.io/badge/Reader-ACS%20ACR1252U-blue)](https://www.acs.com.hk/en/products/3/acr1252u-usb-nfc-reader-ii/)
[![Validated Tag](https://img.shields.io/badge/Validated%20Tag-NXP%20NTAG213-brightgreen)](#tested-tags)

![alt text](screenshots/tui-version/home.png)

A command-line interface for reading and writing NFC tags using the ACS ACR1252U USB NFC Reader on Linux systems.

## Features

- **Read Mode**: Continuously scan NFC tags and automatically open URLs in browser
- **Write Mode**: Write URLs to NFC tags with optional permanent locking
- **Batch Writing**: Write the same URL to multiple tags sequentially
- **Modern TUI**: Beautiful terminal user interface with keyboard shortcuts
- **Cross-platform**: Works on Linux systems with proper NFC reader support

## Hardware Requirements

- ACS ACR1252U USB NFC Reader/Writer (tested)
- NTAG213/215/216 NFC tags (recommended)
- Linux system with USB support

Validated hardware/media:
- Reader: ACS ACR1252U
- Tags: NXP NTAG213 (validated)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ACS-ACR-1252-NFC-CLI-Linux.git
cd ACS-ACR-1252-NFC-CLI-Linux
```

2. Set up the environment using the wrapper script:
```bash
./scripts/install.sh
```

3. Run the application:
```bash
./scripts/run.sh
# or manually
source .venv/bin/activate && python main.py
```

## Usage

### CLI

Reading tags:

![alt text](screenshots/cli-version/reading-tag.png)

Writing & locking operation:

![alt text](screenshots/cli-version/writing-tag.png)

### TUI Mode (Default)

Run the application to launch the terminal user interface:

```bash
./scripts/run.sh
```

**Keyboard Shortcuts:**
- `Ctrl+1`: Switch to Read Mode
- `Ctrl+2`: Switch to Write Mode
- `Ctrl+Q`: Quit application

**Read Mode:**
- Present NFC tag to reader
- URL will be automatically opened in browser
- URL copied to clipboard

**Write Mode:**
1. Enter URL in the input field
2. Optionally set batch count for multiple tags
3. Press Enter or click "Start Writing"
4. Present NFC tag(s) to reader
- MIFARE Ultralight
- MIFARE Classic (with NDEF formatting)
- ISO14443 Type A tags

## Example URLs

The CLI can handle long URLs like:
```
https://example.com/item/6183cbf5-6441-4409-9fb1-eef1eb6f4805
```

## Troubleshooting

### Reader Not Found
- Ensure the ACS ACR1252 is connected via USB
- Check that pcscd daemon is running: `sudo systemctl status pcscd`
- Verify reader is detected: `pcsc_scan`

### Permission Issues
- Add your user to the `scard` group: `sudo usermod -a -G scard $USER`
- Log out and back in for group changes to take effect

### Tag Read/Write Failures
- Ensure tag is NDEF-compatible
- Try different tag positioning on the reader
- Check that the tag isn't locked or damaged

## Tested Tags

- NXP NTAG213: ~144 bytes usable NDEF capacity.

Example tag URLs we’ve used in testing often include a UUID path segment from a Homebox inventory system. For documentation, we avoid exposing the real domain and any sensitive identifiers. Typical UUIDs are 36 characters in 8-4-4-4-12 format (for example only):
```
/item/6183cbf5-6441-4409-9fb1-eef1eb6f4805
```
References to real domains are replaced with a neutral `https://example.com` base.

## Development

### Project Structure
```
├── scripts/           # Bash wrapper scripts (install, run)
├── tools/             # Helper Python tools (e.g., write_url)
├── main.py            # CLI/TUI entry point
├── nfc_cli.py         # CLI interface (interactive)
├── nfc_tui.py         # Textual TUI interface (default)
├── nfc_gui.py         # Simple GUI prototype (Tkinter)
├── nfc_handler.py     # NFC operations and card monitoring
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Reproducible Example

To produce a sanitized, commit‑friendly example of a full write flow without exposing private URLs:

- Write `https://example.com` to a tag and capture logs:
```
python tools/write_url.py
# options: --url <custom-url> --lock --timeout 60
```

This creates two files:
- `debug/ndef_write_<timestamp>.log` (verbose runtime log; ignored by git)
- `examples/ndef_write_example_<timestamp>.txt` (sanitized log suitable for the repo)

### Variants
- TUI (default): `./scripts/run.sh`
- CLI: `./scripts/run_cli.sh`
- GUI: `./scripts/run_gui.sh`

Note: By default, write operations permanently lock tags. There is no on-screen warning. The helper tool `tools/write_url.py` allows opting out by omitting `--lock`.

### Dependencies
- `pyscard`: PC/SC smartcard library interface
- `ndeflib`: NDEF message encoding/decoding
- `textual`: Modern TUI framework
- `click`: Command-line interface creation

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Ensure your hardware is compatible
