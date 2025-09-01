#!/usr/bin/env python3
"""
Simple test script to diagnose NFC card detection issues
"""

import time
from smartcard.System import readers
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString

class TestCardObserver(CardObserver):
    """Simple observer for testing card detection"""
    
    def update(self, observable, actions):
        (addedcards, removedcards) = actions
        
        print(f"\n=== CARD EVENT ===")
        print(f"Time: {time.strftime('%H:%M:%S')}")
        
        if addedcards:
            print(f"✅ Cards ADDED: {len(addedcards)}")
            for i, card in enumerate(addedcards):
                print(f"  Card {i+1}: {card}")
                
                # Try to connect and get basic info
                try:
                    connection = card.createConnection()
                    print(f"  🔄 Attempting connection...")
                    
                    # Try different connection methods
                    connected = False
                    for method in [None, 'T0', 'T1']:
                        try:
                            if method:
                                print(f"    Trying protocol: {method}")
                                connection.connect(protocol=method)
                            else:
                                print(f"    Trying default connection")
                                connection.connect()
                            
                            print(f"    ✅ Connected with {method or 'default'}")
                            connected = True
                            break
                            
                        except Exception as e:
                            print(f"    ❌ {method or 'default'} failed: {e}")
                    
                    if connected:
                        # Get ATR
                        try:
                            atr = connection.getATR()
                            print(f"    📋 ATR: {toHexString(atr)}")
                        except Exception as e:
                            print(f"    ❌ ATR failed: {e}")
                        
                        # Try basic APDU
                        try:
                            # Select NDEF application
                            select_ndef = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01]
                            response, sw1, sw2 = connection.transmit(select_ndef)
                            print(f"    📡 NDEF Select: {toHexString(response)} SW:{sw1:02X}{sw2:02X}")
                        except Exception as e:
                            print(f"    ❌ NDEF select failed: {e}")
                        
                        connection.disconnect()
                        print(f"    🔌 Disconnected")
                    
                except Exception as e:
                    print(f"  ❌ Connection failed: {e}")
        
        if removedcards:
            print(f"📤 Cards REMOVED: {len(removedcards)}")
            for i, card in enumerate(removedcards):
                print(f"  Card {i+1}: {card}")

def main():
    print("🔍 NFC Card Detection Test")
    print("=" * 50)
    
    # Check for readers
    try:
        available_readers = readers()
        if not available_readers:
            print("❌ No card readers found!")
            return
        
        print(f"📡 Found {len(available_readers)} reader(s):")
        for i, reader in enumerate(available_readers):
            print(f"  {i+1}. {reader}")
        
    except Exception as e:
        print(f"❌ Error checking readers: {e}")
        return
    
    print("\n🔄 Starting card monitoring...")
    print("Present your NFC card to the reader...")
    print("Press Ctrl+C to exit")
    
    # Start monitoring
    observer = TestCardObserver()
    monitor = CardMonitor()
    monitor.addObserver(observer)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping monitor...")
        monitor.deleteObserver(observer)
        print("✅ Test complete")

if __name__ == "__main__":
    main()
