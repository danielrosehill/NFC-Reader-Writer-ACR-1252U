#!/usr/bin/env python3
"""
ACS ACR1252 NFC CLI - Main Entry Point
A command-line interface for reading and writing URLs to NFC tags
"""

import sys
import click
from nfc_tui import main as tui_main


@click.command()
@click.option('--version', is_flag=True, help='Show version information')
@click.option('--debug', is_flag=True, help='Enable debug mode - saves raw NDEF data to debug/ folder')
def main(version, debug):
    """
    ACS ACR1252 NFC Reader/Writer CLI
    
    A terminal user interface for reading URLs from NFC tags and writing URLs to NFC tags.
    
    Features:
    - Read mode: Continuously scan for NFC tags and open URLs in browser
    - Write mode: Write URLs to NFC tags and lock them
    - Batch writing: Write the same URL to multiple tags
    - Keyboard shortcuts: Ctrl+1 (Read), Ctrl+2 (Write), Ctrl+R (Reset)
    - Debug mode: Use --debug to save raw card data to debug/ folder
    """
    
    if version:
        click.echo("ACS ACR1252 NFC CLI v1.0.0")
        click.echo("Built for ACS ACR1252 USB NFC Reader/Writer")
        return
    
    if debug:
        click.echo("🐛 Debug mode enabled - raw NDEF data will be saved to debug/ folder")
    
    try:
        # Launch the TUI application
        tui_main(debug_mode=debug)
    except KeyboardInterrupt:
        click.echo("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
