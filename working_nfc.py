#!/usr/bin/env python3
"""
Working NFC implementation based on VladoPortos's proven ACR1252 code
"""

import os
import hashlib
import ndef
import webbrowser
import pyperclip
from typing import Dict, List
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString
from smartcard.CardConnection import CardConnection
from smartcard.System import *

class NFCManager:
    def __init__(self, url: str = "https://example.com", debug: bool = False):
        self.url = url
        self.debug = debug
        self.cards_processed = 0
        self.mode = "read"  # "read" or "write"
        
    def derive_password(self, passphrase: str) -> List[int]:
        """Hash passphrase and return first 4 bytes as password"""
        hasher = hashlib.sha256()
        hasher.update(passphrase.encode())
        return list(hasher.digest()[:4])

    def authenticate_with_password(self, connection: CardConnection, passphrase: str) -> bool:
        """Authenticate with NTAG215 using password"""
        password = self.derive_password(passphrase)
        command = [0xFF, 0x00, 0x00, 0x00, 0x07, 0xD4, 0x42, 0x1B] + password
        response, sw1, sw2 = connection.transmit(command)
        
        if sw1 == 0x90 and sw2 == 0x00 and len(response) >= 5:
            pack = response[3:5]
            print(f"✅ Authentication successful, PACK: {' '.join(f'{byte:02X}' for byte in pack)}")
            return True
        else:
            print("❌ Authentication failed")
            return False

    def create_ndef_record(self, url: str) -> bytes:
        """Create NDEF record from URL"""
        uri_record = ndef.UriRecord(url)
        encoded_message = b''.join(ndef.message_encoder([uri_record]))
        message_length = len(encoded_message)
        
        initial_message = b'\x03' + message_length.to_bytes(1, 'big') + encoded_message + b'\xFE'
        padding_length = -len(initial_message) % 4
        complete_message = initial_message + (b'\x00' * padding_length)
        return complete_message

    def write_ndef_message(self, connection: CardConnection, ndef_message: bytes) -> bool:
        """Write NDEF message to tag"""
        page = 4
        while ndef_message:
            block_data = ndef_message[:4]
            ndef_message = ndef_message[4:]
            write_command = [0xFF, 0xD6, 0x00, page, 0x04] + list(block_data)
            response, sw1, sw2 = connection.transmit(write_command)
            
            if sw1 != 0x90 or sw2 != 0x00:
                print(f"❌ Failed to write to page {page}, SW1: {sw1:02X}, SW2: {sw2:02X}")
                return False
            print(f"✅ Successfully wrote to page {page}")
            page += 1
        return True

    def read_ndef_message(self, connection: CardConnection) -> str:
        """Read NDEF message from tag"""
        try:
            # Read from page 4 onwards (NDEF data area)
            # NTAG213: pages 4-39 (144 bytes), NTAG215: pages 4-129 (504 bytes)
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
            
            if self.debug:
                print(f"🔍 Raw NDEF data: {ndef_data.hex()}")
            
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
                        except Exception as e:
                            if self.debug:
                                print(f"❌ NDEF decode error: {e}")
                            continue
            
            return None
            
        except Exception as e:
            print(f"❌ Error reading NDEF: {e}")
            return None

    def is_password_set(self, connection: CardConnection) -> bool:
        """Check if password protection is enabled"""
        try:
            read_command = [0xFF, 0xB0, 0x00, 0x83, 0x04]
            response, sw1, sw2 = connection.transmit(read_command)
            
            if sw1 == 0x90 and sw2 == 0x00:
                auth0 = response[3]
                return auth0 != 0xFF
            return False
        except:
            return False

    def set_password(self, connection: CardConnection, passphrase: str) -> None:
        """Set password protection on tag (NTAG213/215 compatible)"""
        password = self.derive_password(passphrase)
        pack = [0x00, 0x00]
        
        # NTAG213: PWD at page 0x2A (42), PACK at 0x2B (43), AUTH0 at 0x29 (41)
        # NTAG215: PWD at page 0x85 (133), PACK at 0x86 (134), AUTH0 at 0x83 (131)
        
        try:
            # Try NTAG213 addresses first
            connection.transmit([0xFF, 0xD6, 0x00, 0x2A, 0x04] + password)  # PWD
            connection.transmit([0xFF, 0xD6, 0x00, 0x2B, 0x04] + pack + [0x00, 0x00])  # PACK
            connection.transmit([0xFF, 0xD6, 0x00, 0x29, 0x04, 0x00, 0x00, 0x00, 0x04])  # AUTH0
            print("✅ Password protection set (NTAG213)")
        except:
            try:
                # Fallback to NTAG215 addresses
                connection.transmit([0xFF, 0xD6, 0x00, 0x85, 0x04] + password)
                connection.transmit([0xFF, 0xD6, 0x00, 0x86, 0x04] + pack + [0x00, 0x00])
                connection.transmit([0xFF, 0xD6, 0x00, 0x83, 0x04, 0x00, 0x00, 0x00, 0x04])
                print("✅ Password protection set (NTAG215)")
            except:
                print("❌ Failed to set password protection")

class NFCObserver(CardObserver):
    def __init__(self, nfc_manager: NFCManager):
        self.nfc_manager = nfc_manager
        
    def update(self, observable, actions):
        (addedcards, removedcards) = actions
        
        for card in addedcards:
            print(f"\n📱 Card detected: {toHexString(card.atr)}")
            
            try:
                connection = card.createConnection()
                connection.connect()
                print("🔗 Connected to card")
                
                if self.nfc_manager.mode == "read":
                    self.handle_read_mode(connection)
                elif self.nfc_manager.mode == "write":
                    self.handle_write_mode(connection)
                    
                connection.disconnect()
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        for card in removedcards:
            print("📤 Card removed")
    
    def handle_read_mode(self, connection):
        """Handle reading from NFC tag"""
        print("📖 Reading NDEF data...")
        
        # Try to read without authentication first
        url = self.nfc_manager.read_ndef_message(connection)
        
        if not url:
            # Try with authentication if password might be set
            if self.nfc_manager.is_password_set(connection):
                print("🔐 Tag is password protected, trying authentication...")
                if self.nfc_manager.authenticate_with_password(connection, "defaultpass"):
                    url = self.nfc_manager.read_ndef_message(connection)
        
        if url:
            print(f"✅ URL found: {url}")
            
            # Copy to clipboard
            try:
                pyperclip.copy(url)
                print("📋 URL copied to clipboard")
            except:
                pass
            
            # Open in browser
            try:
                webbrowser.open(url)
                print("🌐 URL opened in browser")
            except:
                pass
        else:
            print("❌ No URL found on tag")
    
    def handle_write_mode(self, connection):
        """Handle writing to NFC tag"""
        print(f"✏️ Writing URL: {self.nfc_manager.url}")
        
        # Check if password is set and authenticate if needed
        if self.nfc_manager.is_password_set(connection):
            if not self.nfc_manager.authenticate_with_password(connection, "defaultpass"):
                print("❌ Authentication failed, cannot write")
                return
        
        # Write NDEF message
        ndef_message = self.nfc_manager.create_ndef_record(self.nfc_manager.url)
        if self.nfc_manager.write_ndef_message(connection, ndef_message):
            print("✅ URL written successfully")
            
            # Set password protection if not already set
            if not self.nfc_manager.is_password_set(connection):
                self.nfc_manager.set_password(connection, "defaultpass")
                
            self.nfc_manager.cards_processed += 1
            print(f"📊 Total cards processed: {self.nfc_manager.cards_processed}")
        else:
            print("❌ Failed to write URL")

def main():
    print("🔍 ACR1252 NFC Reader/Writer")
    print("=" * 40)
    
    # Check for available readers
    available_readers = readers()
    if not available_readers:
        print("❌ No NFC readers found")
        return
    
    print(f"📡 Found readers: {[str(r) for r in available_readers]}")
    
    # Initialize NFC manager
    nfc_manager = NFCManager(debug=True)
    
    print("\n📖 READ MODE - Present NFC tag to read URL")
    print("Commands:")
    print("  'w <url>' - Switch to write mode with URL")
    print("  'r' - Switch to read mode")
    print("  'q' - Quit")
    
    # Start monitoring
    cardmonitor = CardMonitor()
    cardobserver = NFCObserver(nfc_manager)
    cardmonitor.addObserver(cardobserver)
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'r':
                nfc_manager.mode = "read"
                print("📖 Switched to READ mode")
            elif cmd.startswith('w '):
                url = cmd[2:].strip()
                if url:
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    nfc_manager.url = url
                    nfc_manager.mode = "write"
                    print(f"✏️ Switched to WRITE mode with URL: {url}")
                else:
                    print("❌ Please provide a URL")
            else:
                print("❌ Unknown command")
                
    except KeyboardInterrupt:
        pass
    finally:
        cardmonitor.deleteObserver(cardobserver)
        print(f"\n✅ Stopped. Total cards processed: {nfc_manager.cards_processed}")

if __name__ == "__main__":
    main()
