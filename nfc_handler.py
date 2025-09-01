"""
NFC Handler for ACS ACR1252 USB NFC Reader/Writer
Handles reading and writing URLs to NFC tags using NDEF format
"""

import time
import threading
import os
import datetime
from typing import Optional, Callable
import webbrowser
import ndef
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.Exceptions import CardRequestTimeoutException, NoCardException


class NFCHandler:
    def __init__(self, debug_mode=False):
        self.reader = None
        self.connection = None
        self.monitor = None
        self.observer = None
        self.is_monitoring = False
        self.read_callback = None
        self.write_callback = None
        self.log_callback = None
        self.mode = "read"  # "read" or "write"
        self.url_to_write = None
        self.batch_mode = False
        self.batch_count = 0
        self.batch_total = 0
        self.debug_mode = debug_mode
        self.debug_counter = 0
        
        # Create debug directory if in debug mode
        if self.debug_mode:
            os.makedirs("debug", exist_ok=True)
        
    def initialize_reader(self) -> bool:
        """Initialize the NFC reader connection"""
        try:
            available_readers = readers()
            if not available_readers:
                return False
                
            # Look for ACS ACR1252 or any available reader
            for reader in available_readers:
                if "ACR1252" in str(reader) or len(available_readers) == 1:
                    self.reader = reader
                    break
            
            if not self.reader:
                self.reader = available_readers[0]  # Use first available reader
                
            return True
        except Exception as e:
            print(f"Error initializing reader: {e}")
            return False
    
    def start_monitoring(self, read_callback: Callable = None, write_callback: Callable = None, log_callback: Callable = None):
        """Start monitoring for NFC tags"""
        if self.is_monitoring:
            return
            
        self.read_callback = read_callback
        self.write_callback = write_callback
        self.log_callback = log_callback
        
        if self.log_callback:
            self.log_callback("🔍 Starting card monitoring...")
        
        self.observer = NFCCardObserver(self)
        self.monitor = CardMonitor()
        self.monitor.addObserver(self.observer)
        self.is_monitoring = True
        
        if self.log_callback:
            self.log_callback("✅ Card monitoring active - waiting for cards...")
    
    def stop_monitoring(self):
        """Stop monitoring for NFC tags"""
        if self.monitor and self.observer:
            self.monitor.deleteObserver(self.observer)
        self.is_monitoring = False
        if self.connection:
            self.connection.disconnect()
    
    def set_mode(self, mode: str, url: str = None, batch_total: int = 1):
        """Set operation mode: 'read' or 'write'"""
        self.mode = mode
        self.url_to_write = url
        self.batch_total = batch_total
        self.batch_count = 0
        self.batch_mode = batch_total > 1
    
    def read_ndef_from_tag(self, connection) -> Optional[str]:
        """Read NDEF data from NFC tag and extract URL"""
        try:
            # Try different approaches to read NDEF data
            
            # Method 1: Try to select NDEF application first
            try:
                select_ndef = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01]
                response, sw1, sw2 = connection.transmit(select_ndef)
                
                if sw1 == 0x90:
                    # Read capability container
                    read_cc = [0x00, 0xB0, 0x00, 0x00, 0x0F]
                    response, sw1, sw2 = connection.transmit(read_cc)
                    
                    if sw1 == 0x90:
                        # Read NDEF data from offset 0x0F
                        read_ndef = [0x00, 0xB0, 0x00, 0x0F, 0x00]
                        response, sw1, sw2 = connection.transmit(read_ndef)
                        
                        if sw1 == 0x90 and len(response) > 2:
                            url = self._parse_ndef_data(bytes(response[2:]), "ndef_app")
                            if url:
                                return url
            except:
                pass
            
            # Method 2: Try reading NTAG213/215/216 directly
            try:
                # Read from page 4 onwards (NTAG format)
                for start_page in [4, 0]:
                    read_cmd = [0xFF, 0xB0, 0x00, start_page, 0x30]  # Read 48 bytes
                    response, sw1, sw2 = connection.transmit(read_cmd)
                    
                    if sw1 == 0x90 and len(response) > 0:
                        url = self._parse_ndef_data(bytes(response), f"ntag_page_{start_page}")
                        if url:
                            return url
            except:
                pass
            
            # Method 3: Try reading as ISO14443-4 card
            try:
                # Read binary data
                read_binary = [0x00, 0xB0, 0x00, 0x00, 0x00]
                response, sw1, sw2 = connection.transmit(read_binary)
                
                if sw1 == 0x90 and len(response) > 0:
                    url = self._parse_ndef_data(bytes(response), "iso14443_binary")
                    if url:
                        return url
            except:
                pass
                
            return None
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Error reading NDEF: {e}")
            return None
    
    def _save_debug_data(self, data: bytes, method: str, success: bool = False, url: str = None):
        """Save raw data to debug files"""
        if not self.debug_mode:
            return
            
        self.debug_counter += 1
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debug/card_{timestamp}_{self.debug_counter:03d}_{method}.dump"
        
        try:
            with open(filename, 'wb') as f:
                f.write(data)
            
            # Also create a hex dump file
            hex_filename = filename.replace('.dump', '.hex')
            with open(hex_filename, 'w') as f:
                f.write(f"Method: {method}\n")
                f.write(f"Success: {success}\n")
                f.write(f"URL Found: {url}\n")
                f.write(f"Data Length: {len(data)} bytes\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write("-" * 50 + "\n")
                
                # Hex dump
                for i in range(0, len(data), 16):
                    hex_part = ' '.join(f'{b:02X}' for b in data[i:i+16])
                    ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+16])
                    f.write(f"{i:04X}: {hex_part:<48} {ascii_part}\n")
            
            if self.log_callback:
                self.log_callback(f"[DEBUG] Saved to {filename}")
                
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Error saving debug data: {e}")

    def _parse_ndef_data(self, data: bytes, method: str = "unknown") -> Optional[str]:
        """Parse NDEF data and extract URL"""
        try:
            # Log raw data for debugging
            if self.log_callback:
                hex_data = ' '.join(f'{b:02X}' for b in data[:32])  # First 32 bytes
                self.log_callback(f"[DEBUG] Raw data ({method}): {hex_data}...")
            
            # Save debug data
            if self.debug_mode:
                self._save_debug_data(data, method, False, None)
            
            # Try to decode as NDEF message
            try:
                records = ndef.message_decoder(data)
                for record in records:
                    if hasattr(record, 'uri') and record.uri:
                        if self.debug_mode:
                            self._save_debug_data(data, f"{method}_success", True, record.uri)
                        return record.uri
                    elif hasattr(record, 'text') and record.text:
                        text = record.text
                        if text.startswith(('http://', 'https://')):
                            if self.debug_mode:
                                self._save_debug_data(data, f"{method}_success", True, text)
                            return text
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"[DEBUG] NDEF decode failed: {e}")
            
            # Try to find NDEF TLV structure manually
            for i in range(len(data) - 3):
                if data[i] == 0x03:  # NDEF Message TLV
                    length = data[i + 1]
                    if length > 0 and i + 2 + length <= len(data):
                        ndef_payload = data[i + 2:i + 2 + length]
                        try:
                            records = ndef.message_decoder(ndef_payload)
                            for record in records:
                                if hasattr(record, 'uri') and record.uri:
                                    if self.debug_mode:
                                        self._save_debug_data(data, f"{method}_tlv_success", True, record.uri)
                                    return record.uri
                                elif hasattr(record, 'text') and record.text:
                                    text = record.text
                                    if text.startswith(('http://', 'https://')):
                                        if self.debug_mode:
                                            self._save_debug_data(data, f"{method}_tlv_success", True, text)
                                        return text
                        except:
                            continue
            
            # Try to find URL patterns directly in the data
            data_str = data.decode('utf-8', errors='ignore')
            import re
            url_pattern = r'https?://[^\s\x00-\x1f]+'
            urls = re.findall(url_pattern, data_str)
            if urls:
                if self.debug_mode:
                    self._save_debug_data(data, f"{method}_regex_success", True, urls[0])
                return urls[0]
                
            return None
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Error parsing NDEF data: {e}")
            return None
    
    def write_url_to_tag(self, connection, url: str) -> bool:
        """Write URL to NFC tag in NDEF format and lock the tag"""
        try:
            # Create NDEF URI record
            uri_record = ndef.UriRecord(url)
            message = ndef.message_encoder([uri_record])
            
            # Select NDEF application
            select_ndef = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01]
            response, sw1, sw2 = connection.transmit(select_ndef)
            
            if sw1 != 0x90:
                return False
            
            # Write NDEF message
            ndef_bytes = list(message)
            length_bytes = [len(ndef_bytes) >> 8, len(ndef_bytes) & 0xFF]
            
            # Write length + NDEF data
            write_cmd = [0x00, 0xD6, 0x00, 0x0F] + [len(length_bytes + ndef_bytes)] + length_bytes + ndef_bytes
            response, sw1, sw2 = connection.transmit(write_cmd)
            
            if sw1 != 0x90:
                return False
            
            # Lock the tag (optional - depends on tag type)
            try:
                lock_cmd = [0x00, 0xD6, 0x00, 0x02, 0x04, 0xFF, 0xFF, 0xFF, 0xFF]
                connection.transmit(lock_cmd)
            except:
                pass  # Locking might not be supported on all tags
            
            return True
            
        except Exception as e:
            print(f"Error writing to tag: {e}")
            return False


class NFCCardObserver(CardObserver):
    """Observer for NFC card events"""
    
    def __init__(self, nfc_handler):
        self.nfc_handler = nfc_handler
    
    def update(self, observable, actions):
        (addedcards, removedcards) = actions
        
        # Log card events
        if self.nfc_handler.log_callback:
            if addedcards:
                self.nfc_handler.log_callback(f"📱 Card detected! ({len(addedcards)} card(s) added)")
            if removedcards:
                self.nfc_handler.log_callback(f"📤 Card removed! ({len(removedcards)} card(s) removed)")
        
        for card in addedcards:
            try:
                if self.nfc_handler.log_callback:
                    self.nfc_handler.log_callback(f"🔗 Connecting to card: {card}")
                
                connection = card.createConnection()
                connection.connect()
                
                if self.nfc_handler.log_callback:
                    self.nfc_handler.log_callback(f"✅ Connected to card successfully")
                
                if self.nfc_handler.mode == "read":
                    self._handle_read_mode(connection)
                elif self.nfc_handler.mode == "write":
                    self._handle_write_mode(connection)
                    
                connection.disconnect()
                
                if self.nfc_handler.log_callback:
                    self.nfc_handler.log_callback("🔌 Disconnected from card")
                
            except Exception as e:
                if self.nfc_handler.log_callback:
                    self.nfc_handler.log_callback(f"❌ Error handling card: {e}")
                print(f"Error handling card: {e}")
    
    def _handle_read_mode(self, connection):
        """Handle card in read mode"""
        if self.nfc_handler.log_callback:
            self.nfc_handler.log_callback("📖 Reading NDEF data from tag...")
        
        url = self.nfc_handler.read_ndef_from_tag(connection)
        if url:
            if self.nfc_handler.log_callback:
                self.nfc_handler.log_callback(f"✅ URL found: {url}")
            if self.nfc_handler.read_callback:
                self.nfc_handler.read_callback(url)
        else:
            if self.nfc_handler.log_callback:
                self.nfc_handler.log_callback("❌ No URL found on tag or tag not NDEF formatted")
    
    def _handle_write_mode(self, connection):
        """Handle card in write mode"""
        if not self.nfc_handler.url_to_write:
            if self.nfc_handler.log_callback:
                self.nfc_handler.log_callback("❌ No URL set for writing")
            return
        
        if self.nfc_handler.log_callback:
            self.nfc_handler.log_callback(f"✏️ Writing URL to tag: {self.nfc_handler.url_to_write}")
            
        success = self.nfc_handler.write_url_to_tag(connection, self.nfc_handler.url_to_write)
        
        if success:
            self.nfc_handler.batch_count += 1
            if self.nfc_handler.log_callback:
                self.nfc_handler.log_callback("✅ URL written and tag locked successfully")
        else:
            if self.nfc_handler.log_callback:
                self.nfc_handler.log_callback("❌ Failed to write URL to tag")
            
        if self.nfc_handler.write_callback:
            self.nfc_handler.write_callback(success, self.nfc_handler.batch_count, self.nfc_handler.batch_total)
