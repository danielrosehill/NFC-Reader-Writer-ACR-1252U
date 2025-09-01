#!/usr/bin/env python3
"""
Simple test to verify NFC reader detection and basic functionality
"""

from smartcard.System import readers
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString
import time

class SimpleObserver(CardObserver):
    def update(self, observable, actions):
        (addedcards, removedcards) = actions
        
        for card in addedcards:
            print(f"✅ Card detected: {toHexString(card.atr)}")
            
            try:
                connection = card.createConnection()
                connection.connect()
                print("🔗 Connected successfully")
                
                # Try simple read command
                read_cmd = [0xFF, 0xB0, 0x00, 0x00, 0x04]
                response, sw1, sw2 = connection.transmit(read_cmd)
                print(f"📖 Read response: {toHexString(response)} SW:{sw1:02X}{sw2:02X}")
                
                connection.disconnect()
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        for card in removedcards:
            print("📤 Card removed")

def main():
    print("🔍 Simple NFC Reader Test")
    print("=" * 30)
    
    # Check readers
    try:
        available_readers = readers()
        if not available_readers:
            print("❌ No readers found")
            return
        
        print(f"📡 Found {len(available_readers)} reader(s):")
        for i, reader in enumerate(available_readers):
            print(f"  {i+1}. {reader}")
        
    except Exception as e:
        print(f"❌ Error checking readers: {e}")
        return
    
    print("\n📱 Present your NFC card...")
    print("Press Ctrl+C to exit")
    
    # Start monitoring
    observer = SimpleObserver()
    monitor = CardMonitor()
    monitor.addObserver(observer)
    
    try:
        time.sleep(30)  # Wait 30 seconds
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        monitor.deleteObserver(observer)
        print("✅ Test complete")

if __name__ == "__main__":
    main()
