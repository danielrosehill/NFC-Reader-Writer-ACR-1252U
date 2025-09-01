"""
NFC Handler for ACS ACR1252 USB NFC Reader/Writer
Handles reading and writing URLs to NTAG213/215/216 tags
Based on VladoPortos's ACR1252 implementation: https://github.com/VladoPortos/python-nfc-read-write-acr1252
"""

import hashlib
import ndef
import webbrowser
import pyperclip
import time
from typing import Optional, Callable
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.CardConnection import CardConnection
from smartcard.System import readers


class NFCHandler:
    def __init__(self, debug_mode=False):
        self.reader = None
        self.monitor = None
        self.observer = None
        self.is_monitoring = False
        self.read_callback = None
        self.write_callback = None
        self.log_callback = None
        self.mode = "read"  # "read" or "write"
        self.url_to_write = None
        self.batch_count = 0
        self.batch_total = 0
        self.debug_mode = debug_mode
        self.cards_processed = 0
        self.lock_tags = False  # Whether to permanently lock tags after writing
        self.last_read_time = 0  # Timestamp of last successful read
        self.read_cooldown = 3.0  # Cooldown period in seconds
        
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
            if self.log_callback:
                self.log_callback(f"Error initializing reader: {e}")
            return False
            
    def create_ndef_record(self, url: str) -> bytes:
        """Create NDEF record from URL using direct NTAG213 approach"""
        # Create NDEF URI record manually for ACR1252 compatibility
        uri_record = ndef.UriRecord(url)
        encoded_message = b''.join(ndef.message_encoder([uri_record]))
        message_length = len(encoded_message)
        
        # NDEF TLV format: Type(0x03) + Length + Value + Terminator(0xFE)
        ndef_tlv = b'\x03' + message_length.to_bytes(1, 'big') + encoded_message + b'\xFE'
        
        # Pad to 4-byte boundary for NTAG213 page alignment
        padding_length = (4 - (len(ndef_tlv) % 4)) % 4
        complete_message = ndef_tlv + (b'\x00' * padding_length)
        
        return complete_message

    def write_ndef_message(self, connection: CardConnection, ndef_message: bytes) -> bool:
        """Write NDEF message to NTAG213 using direct page commands"""
        try:
            # Start writing from page 4 (NTAG213 user data area)
            page = 4
            max_page = 39  # NTAG213 limit
            
            # Write NDEF message in 4-byte chunks
            while ndef_message and page <= max_page:
                # Get next 4 bytes
                if len(ndef_message) >= 4:
                    block_data = list(ndef_message[:4])
                    ndef_message = ndef_message[4:]
                else:
                    # Pad last block with zeros
                    block_data = list(ndef_message) + [0x00] * (4 - len(ndef_message))
                    ndef_message = b''
                
                # Direct NTAG213 write command
                write_command = [0xFF, 0xD6, 0x00, page, 0x04] + block_data
                response, sw1, sw2 = connection.transmit(write_command)
                
                if sw1 != 0x90 or sw2 != 0x00:
                    if self.log_callback:
                        self.log_callback(f"Failed to write to page {page}: SW1={sw1:02X} SW2={sw2:02X}")
                    return False
                
                page += 1
            
            return True
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Write error: {e}")
            return False

    def read_ndef_message(self, connection: CardConnection) -> str:
        """Read NDEF message from tag"""
        try:
            ndef_data = b''
            max_page = 40  # Safe for both NTAG213 and NTAG215
            
            for page in range(4, max_page):
                read_command = [0xFF, 0xB0, 0x00, page, 0x04]
                response, sw1, sw2 = connection.transmit(read_command)
                
                if sw1 != 0x90 or sw2 != 0x00:
                    break
                    
                ndef_data += bytes(response)
                
                # Check for NDEF terminator
                if 0xFE in response:
                    break
            
            # Find NDEF TLV (Type-Length-Value)
            for i in range(len(ndef_data) - 2):
                if ndef_data[i] == 0x03:  # NDEF Message TLV
                    length = ndef_data[i + 1]
                    if length > 0 and i + 2 + length <= len(ndef_data):
                        ndef_payload = ndef_data[i + 2:i + 2 + length]
                        
                        try:
                            records = list(ndef.message_decoder(ndef_payload))
                            for record in records:
                                if hasattr(record, 'uri') and record.uri:
                                    return record.uri
                                elif hasattr(record, 'text') and record.text:
                                    return record.text
                        except Exception:
                            continue
            
            return None
            
        except Exception:
            return None

    def lock_tag_permanently(self, connection: CardConnection) -> bool:
        """Permanently lock NTAG213 tag by setting lock bits"""
        try:
            # Read current lock status
            read_command = [0xFF, 0xB0, 0x00, 0x02, 0x04]
            response, sw1, sw2 = connection.transmit(read_command)
            
            if sw1 != 0x90 or sw2 != 0x00:
                return False
                
            current_lock = list(response)
            
            # Set lock bits - permanently lock pages 3-15
            current_lock[2] = 0xFF  # Lock pages 3-10
            current_lock[3] = 0xFF  # Lock pages 11-15 and lock bytes
            
            # Write lock bytes - WARNING: IRREVERSIBLE!
            write_command = [0xFF, 0xD6, 0x00, 0x02, 0x04] + current_lock
            response, sw1, sw2 = connection.transmit(write_command)
            
            return sw1 == 0x90 and sw2 == 0x00
                
        except Exception:
            return False
    
    def start_monitoring(self, read_callback: Callable = None, write_callback: Callable = None, log_callback: Callable = None):
        """Start monitoring for NFC tags"""
        if self.is_monitoring:
            return
            
        self.read_callback = read_callback
        self.write_callback = write_callback
        self.log_callback = log_callback
        
        if not self.initialize_reader():
            if self.log_callback:
                self.log_callback("Failed to initialize NFC reader")
            return
            
        self.observer = NFCObserver(self)
        self.monitor = CardMonitor()
        self.monitor.addObserver(self.observer)
        self.is_monitoring = True
        
        if self.log_callback:
            self.log_callback(f"Started monitoring with reader: {self.reader}")
    
    def stop_monitoring(self):
        """Stop monitoring for NFC tags"""
        if not self.is_monitoring:
            return
            
        if self.monitor and self.observer:
            self.monitor.deleteObserver(self.observer)
            
        self.monitor = None
        self.observer = None
        self.is_monitoring = False
        
        if self.log_callback:
            self.log_callback("Stopped NFC monitoring")
            
    def set_write_mode(self, url: str, lock_after_write: bool = False):
        """Set write mode with URL and optional locking"""
        self.mode = "write"
        self.url_to_write = url
        self.lock_tags = lock_after_write
        
    def set_read_mode(self):
        """Set read mode"""
        self.mode = "read"
        self.url_to_write = None
        self.lock_tags = False


class NFCObserver(CardObserver):
    def __init__(self, nfc_handler):
        self.nfc_handler = nfc_handler
        
    def update(self, observable, actions):
        (addedcards, removedcards) = actions
        
        for card in addedcards:
            try:
                connection = card.createConnection()
                connection.connect()
                
                if self.nfc_handler.mode == "read":
                    self.handle_read_mode(connection)
                elif self.nfc_handler.mode == "write":
                    self.handle_write_mode(connection)
                    
                connection.disconnect()
                
            except Exception as e:
                if self.nfc_handler.log_callback:
                    self.nfc_handler.log_callback(f"Error: {e}")
        
        for card in removedcards:
            if self.nfc_handler.log_callback:
                self.nfc_handler.log_callback("Card removed")
    
    def handle_read_mode(self, connection):
        """Handle reading from NFC tag with debouncing"""
        current_time = time.time()
        
        # Check if we're in cooldown period
        if current_time - self.nfc_handler.last_read_time < self.nfc_handler.read_cooldown:
            if self.nfc_handler.log_callback:
                self.nfc_handler.log_callback("Tag read ignored (cooldown period)")
            return
        
        if self.nfc_handler.log_callback:
            self.nfc_handler.log_callback("Reading NFC tag...")
        
        url = self.nfc_handler.read_ndef_message(connection)
        
        if url:
            # Update last read time to start cooldown
            self.nfc_handler.last_read_time = current_time
            
            if self.nfc_handler.read_callback:
                self.nfc_handler.read_callback(url)
            
            # Copy to clipboard and open browser
            try:
                pyperclip.copy(url)
                webbrowser.open(url)
            except:
                pass
        else:
            if self.nfc_handler.log_callback:
                self.nfc_handler.log_callback("No URL found on tag")
    
    def handle_write_mode(self, connection):
        """Handle writing to NFC tag"""
        if not self.nfc_handler.url_to_write:
            return
            
        if self.nfc_handler.log_callback:
            self.nfc_handler.log_callback(f"Writing URL: {self.nfc_handler.url_to_write}")
        
        # Write NDEF message
        ndef_message = self.nfc_handler.create_ndef_record(self.nfc_handler.url_to_write)
        if self.nfc_handler.write_ndef_message(connection, ndef_message):
            success_msg = "URL written successfully"
            
            # Lock tag if requested
            if self.nfc_handler.lock_tags:
                if self.nfc_handler.lock_tag_permanently(connection):
                    success_msg += " and locked permanently"
                else:
                    success_msg += " (lock failed)"
            
            if self.nfc_handler.write_callback:
                self.nfc_handler.write_callback(success_msg)
                
            self.nfc_handler.cards_processed += 1
        else:
            if self.nfc_handler.log_callback:
                self.nfc_handler.log_callback("Failed to write URL")
