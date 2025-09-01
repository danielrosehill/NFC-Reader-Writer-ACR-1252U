#!/usr/bin/env python3
"""
Minimal NFC test to isolate the issue
"""

import time
from smartcard.System import readers
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString

class SimpleObserver(CardObserver):
    def update(self, observable, actions):
        (addedcards, removedcards) = actions
        
        for card in addedcards:
            print(f"\n📱 Card detected: {card}")
            
            try:
                connection = card.createConnection()
                
                # Try T0 protocol first (most reliable for NFC)
                try:
                    print("🔄 Connecting with T0 protocol...")
                    connection.connect(protocol='T0')
                    print("✅ T0 connection successful")
                    
                    # Get ATR
                    atr = connection.getATR()
                    print(f"📋 ATR: {toHexString(atr)}")
                    
                    # Try simple NTAG read (most common NFC tag format)
                    print("📖 Attempting NTAG read...")
                    read_cmd = [0xFF, 0xB0, 0x00, 0x04, 0x10]  # Read 16 bytes from page 4
                    response, sw1, sw2 = connection.transmit(read_cmd)
                    print(f"📡 NTAG Response: {toHexString(response)} SW:{sw1:02X}{sw2:02X}")
                    
                    if sw1 == 0x90:
                        print("✅ NTAG read successful")
                        # Look for NDEF data
                        if len(response) > 0:
                            print(f"🔍 Raw data: {response}")
                            # Check for NDEF TLV (0x03)
                            for i, byte in enumerate(response):
                                if byte == 0x03:
                                    print(f"📝 Found NDEF TLV at position {i}")
                    else:
                        print(f"❌ NTAG read failed: SW={sw1:02X}{sw2:02X}")
                    
                    connection.disconnect()
                    print("🔌 Disconnected")
                    
                except Exception as e:
                    print(f"❌ T0 connection failed: {e}")
                    
                    # Try default connection
                    try:
                        print("🔄 Trying default connection...")
                        connection.connect()
                        print("✅ Default connection successful")
                        connection.disconnect()
                    except Exception as e2:
                        print(f"❌ Default connection failed: {e2}")
                        
            except Exception as e:
                print(f"❌ Card handling failed: {e}")

def main():
    print("🔍 Simple NFC Test")
    print("Present your NFC card...")
    
    # Check readers
    available_readers = readers()
    if not available_readers:
        print("❌ No readers found")
        return
        
    print(f"📡 Found readers: {[str(r) for r in available_readers]}")
    
    observer = SimpleObserver()
    monitor = CardMonitor()
    monitor.addObserver(observer)
    
    try:
        time.sleep(30)  # Wait 30 seconds for card
    except KeyboardInterrupt:
        pass
    finally:
        monitor.deleteObserver(observer)
        print("\n✅ Test complete")

if __name__ == "__main__":
    main()
