"""
TUI Interface for ACS ACR1252 NFC Reader/Writer CLI
Built with Textual for modern terminal user interface
"""

import webbrowser
import asyncio
import pyperclip
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Input, RichLog, Label
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from nfc_handler import NFCHandler


class NFCApp(App):
    """Main NFC TUI Application"""
    
    CSS = """
    .mode-indicator {
        height: 3;
        border: solid $primary;
        margin: 1;
        padding: 1;
    }
    
    .read-mode {
        background: $success;
    }
    
    .write-mode {
        background: $warning;
    }
    
    .status-panel {
        height: 6;
        border: solid $secondary;
        margin: 1;
    }
    
    .input-panel {
        height: 5;
        border: solid $secondary;
        margin: 1;
        display: none;
    }
    
    .log-panel {
        height: 25;
        border: solid $secondary;
        margin: 1;
    }
    
    Button {
        margin: 1;
    }
    
    Input {
        margin: 1;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+1", "set_read_mode", "Read Mode"),
        Binding("ctrl+2", "set_write_mode", "Write Mode"),
        Binding("ctrl+r", "reset", "Reset"),
        Binding("ctrl+shift+c", "copy_last_url", "Copy Last URL"),
    ]
    
    current_mode = reactive("read")
    reader_status = reactive("Disconnected")
    
    def __init__(self, debug_mode=False):
        super().__init__()
        self.nfc_handler = NFCHandler(debug_mode=debug_mode)
        self.url_input = None
        self.batch_input = None
        self.log_widget = None
        self.status_label = None
        self.mode_indicator = None
        self.last_url = None
        self.debug_mode = debug_mode
        
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header()
        
        with Container():
            # Mode indicator
            with Container(classes="mode-indicator read-mode", id="mode-indicator"):
                yield Label("📖 READ MODE - Present NFC tag to read URL", id="mode-label")
            
            # Status panel
            with Container(classes="status-panel"):
                yield Label("Reader Status: Initializing...", id="status-label")
                yield Label("Ready to scan NFC tags", id="ready-label")
            
            # Input panel for write mode
            with Container(classes="input-panel", id="input-panel"):
                with Horizontal():
                    yield Input(placeholder="Enter URL to write to NFC tag...", id="url-input")
                    yield Button("Write Single", id="write-single", variant="primary")
                with Horizontal():
                    yield Input(placeholder="Batch count (optional)", id="batch-input")
                    yield Button("Write Batch", id="batch-write", variant="success")
                # URL preview
                with Container(id="url-preview-container"):
                    yield Label("", id="url-preview", classes="url-preview")
            
            # Control buttons
            with Horizontal():
                yield Button("📖 Read Mode (Ctrl+1)", id="read-mode-btn", variant="success")
                yield Button("✏️ Write Mode (Ctrl+2)", id="write-mode-btn", variant="warning")
                yield Button("📋 Copy URL", id="copy-url-btn", variant="primary")
                yield Button("🔄 Reset", id="reset-btn", variant="default")
                yield Button("❌ Quit", id="quit-btn", variant="error")
            
            # Log panel
            with Container(classes="log-panel"):
                yield RichLog(id="log", highlight=True, markup=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the application"""
        self.url_input = self.query_one("#url-input", Input)
        self.batch_input = self.query_one("#batch-input", Input)
        self.log_widget = self.query_one("#log", RichLog)
        self.status_label = self.query_one("#status-label", Label)
        self.mode_indicator = self.query_one("#mode-indicator", Container)
        self.url_preview = self.query_one("#url-preview", Label)
        
        # Initialize NFC reader
        self.initialize_nfc_reader()
        
        # URL input will be handled via on_input_changed event method
        
        # Start in read mode
        self.action_set_read_mode()
    
    def initialize_nfc_reader(self):
        """Initialize the NFC reader"""
        try:
            if self.nfc_handler.initialize_reader():
                self.status_label.update("Reader Status: Connected ✅")
                self.log_widget.write("✅ NFC Reader initialized successfully")
                self.log_widget.write(f"📡 Using reader: {self.nfc_handler.reader}")
                
                # Start monitoring
                self.nfc_handler.start_monitoring(
                    read_callback=self.on_tag_read,
                    write_callback=self.on_tag_written,
                    log_callback=self.log_live_event
                )
            else:
                self.status_label.update("Reader Status: Not Found ❌")
                self.log_widget.write("❌ No NFC reader found. Please connect ACS ACR1252 or compatible reader.")
        except Exception as e:
            self.status_label.update("Reader Status: Error ❌")
            self.log_widget.write(f"❌ Error initializing reader: {e}")
    
    def on_tag_read(self, url: str):
        """Handle tag read event"""
        self.last_url = url
        self.log_widget.write(f"📖 Tag read: {url}")
        
        # Copy to clipboard
        try:
            pyperclip.copy(url)
            self.log_widget.write(f"📋 URL copied to clipboard: {url}")
        except Exception as e:
            self.log_widget.write(f"❌ Error copying to clipboard: {e}")
        
        # Open in browser
        try:
            webbrowser.open(url)
            self.log_widget.write(f"🌐 Opened URL in browser: {url}")
        except Exception as e:
            self.log_widget.write(f"❌ Error opening URL: {e}")
    
    def log_live_event(self, message: str):
        """Handle live logging events from NFC handler"""
        self.log_widget.write(f"[LIVE] {message}")
    
    def on_tag_written(self, message: str):
        """Handle tag write event"""
        self.log_widget.write(f"✅ {message}")
        self.log_widget.write("📝 Present another tag to write or switch to read mode")
        # TUI stays open for sequential operations
    
    def on_input_changed(self, event) -> None:
        """Handle input changes for URL preview"""
        if event.input.id == "url-input":
            new_value = event.value
            self.log_widget.write(f"DEBUG: URL input changed to: '{new_value}'")
            if new_value.strip():
                # Add https:// if no protocol specified
                display_url = new_value
                if not display_url.startswith(('http://', 'https://')):
                    display_url = 'https://' + display_url
                
                # Truncate long URLs for display
                if len(display_url) > 80:
                    display_url = display_url[:77] + "..."
                
                self.url_preview.update(f"📋 URL to write: {display_url}")
            else:
                self.url_preview.update("")
    
    def action_set_read_mode(self):
        """Switch to read mode"""
        self.current_mode = "read"
        self.nfc_handler.set_read_mode()
        
        # Update UI
        self.mode_indicator.remove_class("write-mode")
        self.mode_indicator.add_class("read-mode")
        self.query_one("#mode-label", Label).update("📖 READ MODE - Present NFC tag to read URL")
        self.query_one("#input-panel", Container).styles.display = "none"
        self.url_preview.update("")  # Clear URL preview in read mode
        
        self.log_widget.write("📖 Switched to READ mode")
        self.log_widget.write(f"DEBUG: TUI mode set to: {self.current_mode}")
        self.log_widget.write(f"DEBUG: NFC handler mode: {self.nfc_handler.mode}")
    
    def action_set_write_mode(self):
        """Switch to write mode"""
        self.current_mode = "write"
        
        # Update UI
        self.mode_indicator.remove_class("read-mode")
        self.mode_indicator.add_class("write-mode")
        self.query_one("#mode-label", Label).update("✏️ WRITE MODE - Enter URL and present NFC tag")
        self.query_one("#input-panel", Container).styles.display = "block"
        
        # Update URL preview if there's already text in the input
        current_url = self.url_input.value
        if current_url.strip():
            # Manually trigger URL preview update
            if current_url.strip():
                display_url = current_url
                if not display_url.startswith(('http://', 'https://')):
                    display_url = 'https://' + display_url
                if len(display_url) > 80:
                    display_url = display_url[:77] + "..."
                self.url_preview.update(f"📋 URL to write: {display_url}")
        
        self.log_widget.write("✏️ Switched to WRITE mode")
        self.log_widget.write(f"DEBUG: TUI mode set to: {self.current_mode}")
    
    def action_copy_last_url(self):
        """Copy the last read URL to clipboard"""
        if self.last_url:
            try:
                pyperclip.copy(self.last_url)
                self.log_widget.write(f"📋 Copied to clipboard: {self.last_url}")
            except Exception as e:
                self.log_widget.write(f"❌ Error copying to clipboard: {e}")
        else:
            self.log_widget.write("❌ No URL to copy - read a tag first")
    
    def action_reset(self):
        """Reset the application"""
        self.log_widget.clear()
        self.url_input.value = ""
        self.batch_input.value = ""
        self.last_url = None
        self.log_widget.write("🔄 Application reset")
    
    def action_quit(self):
        """Quit the application"""
        self.nfc_handler.stop_monitoring()
        self.exit()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        button_id = event.button.id
        
        self.log_widget.write(f"DEBUG: Button pressed: {button_id}")
        
        if button_id == "read-mode-btn":
            self.action_set_read_mode()
        elif button_id == "write-mode-btn":
            self.action_set_write_mode()
        elif button_id == "reset-btn":
            self.action_reset()
        elif button_id == "quit-btn":
            self.action_quit()
        elif button_id == "write-single":
            self.log_widget.write("DEBUG: Calling write_single_tag")
            self.write_single_tag()
        elif button_id == "batch-write":
            self.log_widget.write("DEBUG: Calling write_batch_tags")
            self.write_batch_tags()
        elif button_id == "copy-url-btn":
            self.action_copy_last_url()
    
    def write_single_tag(self):
        """Write single tag"""
        url = self.url_input.value.strip()
        if not url:
            self.log_widget.write("❌ Please enter a URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Print URL to terminal for verification
        self.log_widget.write(f"📋 URL to write: {url}")
        print(f"\n📋 URL to write: {url}\n")  # Also print to terminal
        
        # Set write mode and start writing with permanent locking
        self.nfc_handler.set_write_mode(url, lock_after_write=True)
        self.log_widget.write("📝 Present NFC tag to write and permanently lock...")
        self.log_widget.write("⚠️  WARNING: Tag will be PERMANENTLY LOCKED (irreversible!)")
        
        # Reset batch counters for single write
        self.nfc_handler.batch_count = 0
        self.nfc_handler.batch_total = 1
        
        # Update the mode to write explicitly
        self.current_mode = "write"
        
        # Debug: log current state
        self.log_widget.write(f"DEBUG: TUI mode set to: {self.current_mode}")
        self.log_widget.write(f"DEBUG: NFC handler mode: {self.nfc_handler.mode}")
    
    def write_batch_tags(self):
        """Write batch of tags"""
        url = self.url_input.value.strip()
        if not url:
            self.log_widget.write("❌ Please enter a URL")
            return
        
        batch_count_str = self.batch_input.value.strip()
        try:
            batch_count = int(batch_count_str) if batch_count_str else 1
            if batch_count < 1:
                batch_count = 1
        except ValueError:
            self.log_widget.write("❌ Invalid batch count, using 1")
            batch_count = 1
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Print URL to terminal for verification
        self.log_widget.write(f"📋 URL to write: {url}")
        self.log_widget.write(f"📦 Batch count: {batch_count}")
        print(f"\n📋 URL to write: {url}")
        print(f"📦 Batch count: {batch_count}\n")
        
        # Set write mode and start batch writing with permanent locking
        self.nfc_handler.set_write_mode(url, lock_after_write=True)
        self.nfc_handler.batch_count = 0
        self.nfc_handler.batch_total = batch_count
        self.log_widget.write(f"📝 Present first NFC tag (1/{batch_count})...")
        self.log_widget.write("⚠️  WARNING: Tags will be PERMANENTLY LOCKED (irreversible!)")
        
        # Debug: log current state
        self.log_widget.write(f"DEBUG: TUI mode set to: {self.current_mode}")
        self.log_widget.write(f"DEBUG: NFC handler mode: {self.nfc_handler.mode}")


def main(debug_mode=False):
    """Main entry point"""
    app = NFCApp(debug_mode=debug_mode)
    app.run()


if __name__ == "__main__":
    main()
