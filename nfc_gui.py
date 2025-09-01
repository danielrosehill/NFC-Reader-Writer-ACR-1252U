#!/usr/bin/env python3
"""
Simple GUI for ACS ACR1252 NFC Reader/Writer
Built with tkinter for easy URL pasting and NFC operations
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import webbrowser
import pyperclip
from nfc_handler import NFCHandler


class NFCGui:
    def __init__(self, root):
        self.root = root
        self.root.title("ACS ACR1252 NFC Reader/Writer")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Initialize NFC handler
        self.nfc_handler = NFCHandler(debug_mode=True)
        self.current_mode = "read"
        self.last_url = None
        
        # Create GUI elements
        self.create_widgets()
        
        # Initialize NFC reader in background
        threading.Thread(target=self.initialize_nfc, daemon=True).start()
    
    def create_widgets(self):
        """Create the GUI layout"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Reader Status", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Initializing...", foreground="orange")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.mode_label = ttk.Label(status_frame, text="📖 READ MODE", font=("Arial", 12, "bold"))
        self.mode_label.grid(row=0, column=1, sticky=tk.E)
        
        # Mode selection
        mode_frame = ttk.LabelFrame(main_frame, text="Mode Selection", padding="10")
        mode_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(mode_frame, text="📖 Read Mode", command=self.set_read_mode).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(mode_frame, text="✏️ Write Mode", command=self.set_write_mode).grid(row=0, column=1)
        
        # URL input section (for write mode)
        self.url_frame = ttk.LabelFrame(main_frame, text="URL Input", padding="10")
        self.url_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.url_frame.columnconfigure(0, weight=1)
        
        # URL entry with paste button
        url_input_frame = ttk.Frame(self.url_frame)
        url_input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        url_input_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_input_frame, font=("Arial", 11))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.url_entry.bind('<KeyRelease>', self.on_url_change)
        
        ttk.Button(url_input_frame, text="📋 Paste", command=self.paste_url).grid(row=0, column=1)
        
        # URL preview
        self.url_preview = ttk.Label(self.url_frame, text="", foreground="blue", wraplength=700)
        self.url_preview.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Write buttons
        button_frame = ttk.Frame(self.url_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0))
        
        ttk.Button(button_frame, text="✏️ Write Single Tag", command=self.write_single_tag).grid(row=0, column=0, padx=(0, 10))
        
        # Batch count entry
        ttk.Label(button_frame, text="Batch:").grid(row=0, column=1, padx=(10, 5))
        self.batch_entry = ttk.Entry(button_frame, width=5)
        self.batch_entry.grid(row=0, column=2, padx=(0, 10))
        ttk.Button(button_frame, text="📦 Write Batch", command=self.write_batch_tags).grid(row=0, column=3)
        
        # Hide URL frame initially (read mode)
        self.url_frame.grid_remove()
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        ttk.Button(control_frame, text="📋 Copy Last URL", command=self.copy_last_url).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(control_frame, text="🔄 Clear Log", command=self.clear_log).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(control_frame, text="❌ Exit", command=self.on_closing).grid(row=0, column=2)
        
        # Configure main frame row weights
        main_frame.rowconfigure(3, weight=1)
    
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Also print to console for debugging
        print(log_entry.strip())
    
    def initialize_nfc(self):
        """Initialize NFC reader in background thread"""
        try:
            if self.nfc_handler.initialize_reader():
                self.root.after(0, lambda: self.status_label.config(text="Connected ✅", foreground="green"))
                self.root.after(0, lambda: self.log_message(f"✅ NFC Reader initialized: {self.nfc_handler.reader}"))
                
                # Start monitoring
                self.nfc_handler.start_monitoring(
                    read_callback=self.on_tag_read,
                    write_callback=self.on_tag_written,
                    log_callback=self.log_message
                )
            else:
                self.root.after(0, lambda: self.status_label.config(text="Not Found ❌", foreground="red"))
                self.root.after(0, lambda: self.log_message("❌ No NFC reader found. Please connect ACS ACR1252."))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text="Error ❌", foreground="red"))
            self.root.after(0, lambda: self.log_message(f"❌ Error initializing reader: {e}"))
    
    def on_tag_read(self, url):
        """Handle tag read event"""
        self.last_url = url
        self.root.after(0, lambda: self.log_message(f"📖 Tag read: {url}"))
        
        # Copy to clipboard and open browser
        try:
            pyperclip.copy(url)
            self.root.after(0, lambda: self.log_message(f"📋 URL copied to clipboard"))
            webbrowser.open(url)
            self.root.after(0, lambda: self.log_message(f"🌐 Opened in browser"))
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Error: {e}"))
    
    def on_tag_written(self, message):
        """Handle tag write event"""
        self.root.after(0, lambda: self.log_message(f"✅ {message}"))
        self.root.after(0, lambda: self.log_message("📝 Present another tag or switch to read mode"))
    
    def set_read_mode(self):
        """Switch to read mode"""
        self.current_mode = "read"
        self.nfc_handler.set_read_mode()
        
        self.mode_label.config(text="📖 READ MODE", foreground="green")
        self.url_frame.grid_remove()
        self.log_message("📖 Switched to READ mode")
    
    def set_write_mode(self):
        """Switch to write mode"""
        self.current_mode = "write"
        
        self.mode_label.config(text="✏️ WRITE MODE", foreground="orange")
        self.url_frame.grid()
        self.log_message("✏️ Switched to WRITE mode")
        
        # Focus on URL entry
        self.url_entry.focus_set()
    
    def on_url_change(self, event=None):
        """Handle URL entry changes"""
        url = self.url_entry.get().strip()
        if url:
            display_url = url
            if not display_url.startswith(('http://', 'https://')):
                display_url = 'https://' + display_url
            
            # Wrap long URLs
            if len(display_url) > 80:
                display_url = display_url[:77] + "..."
            
            self.url_preview.config(text=f"📋 URL to write: {display_url}")
        else:
            self.url_preview.config(text="")
    
    def paste_url(self):
        """Paste URL from clipboard"""
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, clipboard_content.strip())
                self.on_url_change()
                self.log_message(f"📋 Pasted URL from clipboard")
        except Exception as e:
            self.log_message(f"❌ Error pasting from clipboard: {e}")
    
    def write_single_tag(self):
        """Write single tag"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a URL to write")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Print URL to console and log for verification
        self.log_message(f"📋 URL to write: {url}")
        print(f"\n📋 URL to write: {url}\n")  # Console output for verification
        
        # Set write mode and start writing
        self.nfc_handler.set_write_mode(url, lock_after_write=False)
        self.log_message("📝 Present NFC tag to write URL...")
        
        # Reset batch counters
        self.nfc_handler.batch_count = 0
        self.nfc_handler.batch_total = 1
    
    def write_batch_tags(self):
        """Write batch of tags"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a URL to write")
            return
        
        batch_count_str = self.batch_entry.get().strip()
        try:
            batch_count = int(batch_count_str) if batch_count_str else 1
            if batch_count < 1:
                batch_count = 1
        except ValueError:
            messagebox.showwarning("Invalid Batch Count", "Please enter a valid number")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Print URL and batch info for verification
        self.log_message(f"📋 URL to write: {url}")
        self.log_message(f"📦 Batch count: {batch_count}")
        print(f"\n📋 URL to write: {url}")
        print(f"📦 Batch count: {batch_count}\n")
        
        # Set write mode and start batch writing
        self.nfc_handler.set_write_mode(url, lock_after_write=False)
        self.nfc_handler.batch_count = 0
        self.nfc_handler.batch_total = batch_count
        self.log_message(f"📝 Present first NFC tag (1/{batch_count})...")
    
    def copy_last_url(self):
        """Copy last read URL to clipboard"""
        if self.last_url:
            try:
                pyperclip.copy(self.last_url)
                self.log_message(f"📋 Copied to clipboard: {self.last_url}")
            except Exception as e:
                self.log_message(f"❌ Error copying to clipboard: {e}")
        else:
            messagebox.showinfo("No URL", "No URL to copy - read a tag first")
    
    def clear_log(self):
        """Clear the activity log"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("🔄 Log cleared")
    
    def on_closing(self):
        """Handle application closing"""
        self.nfc_handler.stop_monitoring()
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = NFCGui(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main()
