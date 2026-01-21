#!/usr/bin/env python3
"""Test script to try different serial command formats."""
import serial
import time
import sys

PORT = '/dev/cu.usbmodem40768801'
BAUDRATE = 115200

# Different command formats to test
COMMANDS_TO_TEST = [
    "SET,1,128",
    "SET 1,128", 
    "1,128",
    "SET1,128",
    "SET,1,128\r\n",
    "SET 1,128\r\n",
]

def test_command(ser, command):
    """Send a command and read response."""
    print(f"\n{'='*60}")
    print(f"Testing: {repr(command)}")
    print(f"{'='*60}")
    
    try:
        # Send command
        ser.write(command.encode('ascii'))
        if not command.endswith('\r\n'):
            ser.write(b'\r\n')
        
        print(f"Sent: {command}")
        
        # Wait a bit for response
        time.sleep(0.5)
        
        # Read response
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
            print(f"Response: {response.strip()}")
        else:
            print("No response received")
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    try:
        print(f"Connecting to {PORT} at {BAUDRATE} baud...")
        ser = serial.Serial(PORT, BAUDRATE, timeout=2)
        print("Connected!\n")
        
        # Give device time to initialize
        time.sleep(1)
        
        # Clear any existing data
        ser.reset_input_buffer()
        
        print("Testing different command formats...")
        print("(You can also type commands manually - press Ctrl+C to exit)\n")
        
        # Test each command format
        for cmd in COMMANDS_TO_TEST:
            test_command(ser, cmd)
            time.sleep(0.5)  # Brief pause between commands
        
        print(f"\n{'='*60}")
        print("Manual testing mode - type commands directly:")
        print("(Format: command then Enter, or 'quit' to exit)")
        print(f"{'='*60}\n")
        
        # Interactive mode
        while True:
            try:
                user_input = input("Enter command: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                if user_input:
                    test_command(ser, user_input)
            except KeyboardInterrupt:
                break
        
    except serial.SerialException as e:
        print(f"Error connecting to serial port: {e}")
        print(f"\nMake sure:")
        print(f"1. Device is connected at {PORT}")
        print(f"2. No other program is using the serial port")
        print(f"3. Try: ls -la {PORT}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed")

if __name__ == "__main__":
    main()
