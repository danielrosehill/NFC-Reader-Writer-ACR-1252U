#!/usr/bin/env python3
"""
Test script for ACS ACR1252 NFC CLI
Tests the CLI without requiring actual NFC hardware
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import smartcard
        print("✅ pyscard imported successfully")
    except ImportError as e:
        print(f"❌ pyscard import failed: {e}")
        return False
    
    try:
        import ndef
        print("✅ ndeflib imported successfully")
    except ImportError as e:
        print(f"❌ ndeflib import failed: {e}")
        return False
    
    try:
        import textual
        print("✅ textual imported successfully")
    except ImportError as e:
        print(f"❌ textual import failed: {e}")
        return False
    
    try:
        import click
        print("✅ click imported successfully")
    except ImportError as e:
        print(f"❌ click import failed: {e}")
        return False
    
    return True

def test_modules():
    """Test that our modules can be imported"""
    print("\nTesting custom modules...")
    
    try:
        from nfc_handler import NFCHandler
        print("✅ NFCHandler imported successfully")
    except ImportError as e:
        print(f"❌ NFCHandler import failed: {e}")
        return False
    
    try:
        from nfc_tui import NFCApp
        print("✅ NFCApp imported successfully")
    except ImportError as e:
        print(f"❌ NFCApp import failed: {e}")
        return False
    
    return True

def test_nfc_handler():
    """Test NFCHandler initialization"""
    print("\nTesting NFCHandler...")
    
    try:
        from nfc_handler import NFCHandler
        handler = NFCHandler()
        print("✅ NFCHandler created successfully")
        
        # Test mode setting
        handler.set_mode("read")
        assert handler.mode == "read"
        print("✅ Read mode set successfully")
        
        handler.set_mode("write", "https://example.com", 5)
        assert handler.mode == "write"
        assert handler.url_to_write == "https://example.com"
        assert handler.batch_total == 5
        print("✅ Write mode set successfully")
        
        return True
    except Exception as e:
        print(f"❌ NFCHandler test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("ACS ACR1252 NFC CLI - Test Suite")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_modules():
        tests_passed += 1
    
    if test_nfc_handler():
        tests_passed += 1
    
    print(f"\n{'=' * 40}")
    print(f"Tests completed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! CLI is ready to use.")
        print("\nTo start the CLI:")
        print("  python main.py")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
