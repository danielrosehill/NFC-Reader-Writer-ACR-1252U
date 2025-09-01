#!/usr/bin/env python3
"""
Simple NFC test using nfcpy library - much cleaner approach
"""

import nfc
import ndef
import time
import threading
from typing import Optional

def on_connect(tag):
    """Handle NFC tag connection"""
    print(f"\n📱 Tag detected: {tag}")
    print(f"🔍 Tag type: {type(tag).__name__}")
    
    # Check if tag has NDEF capability
    if tag.ndef is not None:
        print(f"📝 NDEF capable: {tag.ndef.is_readable}")
        
        if tag.ndef.is_readable and len(tag.ndef.octets) > 0:
            print(f"📖 Reading NDEF data ({len(tag.ndef.octets)} bytes)...")
            
            try:
                # Parse NDEF records
                records = list(ndef.message_decoder(tag.ndef.octets))
                print(f"✅ Found {len(records)} NDEF record(s)")
                
                for i, record in enumerate(records):
                    print(f"  Record {i+1}: {type(record).__name__}")
                    
                    if hasattr(record, 'uri'):
                        print(f"    📎 URL: {record.uri}")
                        return record.uri
                    elif hasattr(record, 'text'):
                        print(f"    📄 Text: {record.text}")
                        return record.text
                        
            except Exception as e:
                print(f"❌ Error parsing NDEF: {e}")
        else:
            print("📭 No NDEF data found")
    else:
        print("❌ Tag is not NDEF capable")
    
    return True

def write_url_to_tag(tag, url: str) -> bool:
    """Write URL to NFC tag"""
    if tag.ndef is None:
        print("❌ Tag is not NDEF capable")
        return False
        
    if not tag.ndef.is_writeable:
        print("❌ Tag is not writeable")
        return False
    
    try:
        # Create NDEF URI record
        uri_record = ndef.UriRecord(url)
        message = [uri_record]
        
        # Write to tag
        tag.ndef.records = message
        print(f"✅ Successfully wrote URL: {url}")
        return True
        
    except Exception as e:
        print(f"❌ Error writing to tag: {e}")
        return False

def main():
    print("🔍 NFC Test using nfcpy")
    print("=" * 40)
    
    try:
        # Try to open NFC device
        clf = nfc.ContactlessFrontend('usb')
        print(f"📡 NFC device opened: {clf}")
        
        print("\n📖 READ MODE - Present NFC tag to read...")
        print("Press Ctrl+C to exit")
        
        while True:
            try:
                # Wait for tag
                tag = clf.connect(rdwr={'on-connect': on_connect})
                if tag:
                    print("📤 Tag removed")
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTrying alternative connection methods...")
        
        # Try different connection strings
        for conn_str in ['usb:072f:223b', 'usb:072f', 'tty:USB0', 'tty:AMA0']:
            try:
                print(f"🔄 Trying: {conn_str}")
                clf = nfc.ContactlessFrontend(conn_str)
                print(f"✅ Connected with: {conn_str}")
                
                tag = clf.connect(rdwr={'on-connect': on_connect})
                break
                
            except Exception as e2:
                print(f"❌ {conn_str} failed: {e2}")
                continue
    
    finally:
        try:
            clf.close()
            print("🔌 NFC device closed")
        except:
            pass

if __name__ == "__main__":
    main()
