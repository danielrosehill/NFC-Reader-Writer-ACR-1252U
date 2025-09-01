#!/usr/bin/env python3
"""
Simple CLI for ACS ACR1252 NFC Reader/Writer
Better URL input handling with clipboard support
"""

import sys
import threading
import time
import webbrowser
import pyperclip
from nfc_handler import NFCHandler


class NFCCli:
    def __init__(self, debug_mode=False):
        self.nfc_handler = NFCHandler(debug_mode=debug_mode)
        self.current_mode = "read"
        self.last_url = None
        self.running = True
        
    def log_message(self, message):
        """Print timestamped message"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def initialize_nfc(self):
        """Initialize NFC reader"""
        try:
            if self.nfc_handler.initialize_reader():
                self.log_message(f"✅ NFC Reader initialized: {self.nfc_handler.reader}")
                
                # Start monitoring
                self.nfc_handler.start_monitoring(
                    read_callback=self.on_tag_read,
                    write_callback=self.on_tag_written,
                    log_callback=self.log_message
                )
                return True
            else:
                self.log_message("❌ No NFC reader found. Please connect ACS ACR1252.")
                return False
        except Exception as e:
            self.log_message(f"❌ Error initializing reader: {e}")
            return False
    
    def on_tag_read(self, url):
        """Handle tag read event"""
        self.last_url = url
        self.log_message(f"📖 Tag read: {url}")
        
        # Copy to clipboard and open browser
        try:
            pyperclip.copy(url)
            self.log_message(f"📋 URL copied to clipboard")
            webbrowser.open(url)
            self.log_message(f"🌐 Opened in browser")
        except Exception as e:
            self.log_message(f"❌ Error: {e}")
        
        print("\n" + "="*60)
        self.show_menu()
    
    def on_tag_written(self, message):
        """Handle tag write event"""
        self.log_message(f"✅ {message}")
        self.log_message("📝 Present another tag or choose a different option")
        
        print("\n" + "="*60)
        self.show_menu()
    
    def show_menu(self):
        """Display main menu"""
        print(f"\n🔧 ACS ACR1252 NFC Reader/Writer")
        print(f"📡 Reader Status: Connected ✅")
        print(f"🎯 Current Mode: {self.current_mode.upper()}")
        
        if self.last_url:
            print(f"📋 Last URL: {self.last_url}")
        
        print("\nOptions:")
        print("1. 📖 Read Mode - Present NFC tag to read")
        print("2. ✏️  Write Mode - Write URL to NFC tag")
        print("3. 📋 Copy last URL to clipboard")
        print("4. ❌ Exit")
        print("\nChoice (1-4): ", end="", flush=True)
    
    def get_url_input(self):
        """Get URL input with paste support"""
        print("\n📝 URL Input Options:")
        print("1. Type URL manually")
        print("2. Paste from clipboard")
        print("3. Cancel")
        
        while True:
            choice = input("\nChoice (1-3): ").strip()
            
            if choice == "1":
                url = input("Enter URL: ").strip()
                if url:
                    return url
                print("❌ Please enter a valid URL")
                
            elif choice == "2":
                try:
                    clipboard_content = pyperclip.paste().strip()
                    if clipboard_content:
                        print(f"📋 Clipboard content: {clipboard_content}")
                        confirm = input("Use this URL? (y/n): ").strip().lower()
                        if confirm in ['y', 'yes']:
                            return clipboard_content
                    else:
                        print("❌ Clipboard is empty")
                except Exception as e:
                    print(f"❌ Error accessing clipboard: {e}")
                    
            elif choice == "3":
                return None
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    def write_mode(self):
        """Handle write mode"""
        url = self.get_url_input()
        if not url:
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Show URL clearly for verification
        print(f"\n📋 URL to write: {url}")
        print("="*len(url) + "="*20)
        print("⚠️  WARNING: Tags will be PERMANENTLY LOCKED after writing (irreversible!)")
        
        confirm = input("Write and permanently lock this URL to NFC tag? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ Write cancelled")
            return
        
        # Ask about batch writing
        batch_input = input("Batch count (press Enter for single tag): ").strip()
        try:
            batch_count = int(batch_input) if batch_input else 1
            if batch_count < 1:
                batch_count = 1
        except ValueError:
            batch_count = 1
        
        if batch_count > 1:
            print(f"📦 Batch write: {batch_count} tags")
        
        # Set write mode and start writing with permanent locking
        self.nfc_handler.set_write_mode(url, lock_after_write=True)
        self.nfc_handler.batch_count = 0
        self.nfc_handler.batch_total = batch_count
        
        if batch_count > 1:
            self.log_message(f"📝 Present first NFC tag (1/{batch_count})...")
        else:
            self.log_message("📝 Present NFC tag to write URL...")
        
        # Wait for tag operations
        print("Waiting for NFC tag... (Press Ctrl+C to cancel)")
    
    def run(self):
        """Main application loop"""
        print("🚀 Starting ACS ACR1252 NFC Reader/Writer...")
        
        if not self.initialize_nfc():
            print("❌ Failed to initialize NFC reader. Exiting.")
            return
        
        # Start in read mode
        self.nfc_handler.set_read_mode()
        self.current_mode = "read"
        
        try:
            self.show_menu()
            
            while self.running:
                try:
                    choice = input().strip()
                    
                    if choice == "1":
                        self.current_mode = "read"
                        self.nfc_handler.set_read_mode()
                        self.log_message("📖 Switched to READ mode")
                        self.log_message("📝 Present NFC tag to read...")
                        
                    elif choice == "2":
                        self.current_mode = "write"
                        self.write_mode()
                        
                    elif choice == "3":
                        if self.last_url:
                            try:
                                pyperclip.copy(self.last_url)
                                self.log_message(f"📋 Copied to clipboard: {self.last_url}")
                            except Exception as e:
                                self.log_message(f"❌ Error copying to clipboard: {e}")
                        else:
                            print("❌ No URL to copy - read a tag first")
                        
                        print("\n" + "="*60)
                        self.show_menu()
                        
                    elif choice == "4":
                        self.running = False
                        break
                        
                    else:
                        print("❌ Invalid choice. Please enter 1-4.")
                        self.show_menu()
                        
                except KeyboardInterrupt:
                    print("\n\n🔄 Returning to menu...")
                    print("="*60)
                    self.show_menu()
                    
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            
        finally:
            self.nfc_handler.stop_monitoring()
            print("✅ NFC monitoring stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ACS ACR1252 NFC Reader/Writer CLI")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    app = NFCCli(debug_mode=args.debug)
    app.run()


if __name__ == "__main__":
    main()
