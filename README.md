# ACS ACR1252 NFC CLI

A modern command-line interface for the ACS ACR1252 USB NFC Reader/Writer. This CLI provides an intuitive terminal user interface (TUI) for reading URLs from NFC tags and writing URLs to NFC tags with batch support.

## Features

- **📖 Read Mode**: Continuously scan NFC tags and automatically open URLs in your browser
- **✏️ Write Mode**: Write URLs to NFC tags with automatic tag locking
- **📦 Batch Writing**: Write the same URL to multiple tags sequentially
- **⌨️ Keyboard Shortcuts**: Quick mode switching with Ctrl+1 (Read) and Ctrl+2 (Write)
- **🎨 Modern TUI**: Beautiful terminal interface built with Textual
- **🔒 Tag Locking**: Automatically locks tags after writing to prevent accidental overwrites
- **🌐 Long URL Support**: Handles long URLs like the example in your repository

## Requirements

- Python 3.8+
- ACS ACR1252 USB NFC Reader/Writer (or compatible PC/SC reader)
- Linux system with PC/SC daemon (pcscd)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/danielrosehill/ACS-ACR-1252-NFC-CLI-Linux.git
   cd ACS-ACR-1252-NFC-CLI-Linux
   ```

2. **Set up virtual environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Ensure PC/SC daemon is running**:
   ```bash
   sudo systemctl start pcscd
   sudo systemctl enable pcscd
   ```

## Usage

### Starting the CLI

```bash
python main.py
```

Or with the executable:
```bash
./main.py
```

### Interface Overview

The TUI interface consists of:
- **Mode Indicator**: Shows current mode (Read/Write) with color coding
- **Status Panel**: Displays reader connection status
- **Input Panel**: URL input and batch controls (visible in write mode)
- **Control Buttons**: Mode switching and application controls
- **Log Panel**: Real-time activity log with status messages

### Operating Modes

#### Read Mode (Default)
- Automatically activated on startup
- Present any NFC tag to the reader
- URLs are decoded and opened in your default browser
- Continuous operation - no need to restart after each tag

**Keyboard Shortcut**: `Ctrl+1`

#### Write Mode
- Enter a URL in the input field
- Choose single write or batch write
- Present NFC tag(s) to write the URL
- Tags are automatically locked after writing

**Keyboard Shortcut**: `Ctrl+2`

### Batch Writing

1. Switch to Write Mode
2. Enter the URL to write
3. Enter the number of tags in the "Batch count" field
4. Click "Write Batch"
5. Present tags one by one as prompted

### Keyboard Shortcuts

- `Ctrl+1`: Switch to Read Mode
- `Ctrl+2`: Switch to Write Mode  
- `Ctrl+R`: Reset application (clear logs and inputs)
- `Ctrl+C`: Quit application

## Supported NFC Tags

The CLI supports NDEF-compatible NFC tags including:
- NTAG213/215/216
- MIFARE Ultralight
- MIFARE Classic (with NDEF formatting)
- ISO14443 Type A tags

## Example URLs

The CLI can handle long URLs like:
```
https://homebox.residencejlm.com/item/6183cbf5-6441-4409-9fb1-eef1eb6f4805
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

## Development

### Project Structure
```
├── main.py           # CLI entry point
├── nfc_handler.py    # NFC operations and card monitoring
├── nfc_tui.py        # Textual TUI interface
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

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
