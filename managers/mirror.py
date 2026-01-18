#!/usr/bin/env python3
"""
Mirror Manager - scrcpy and wireless ADB functions
"""

import shutil
import subprocess

from common_utils import (
    RED, GREEN, YELLOW, BLUE, NC,
    is_windows, is_macos, is_linux,
)
from core.constants import PATTERNS
from core.state import get_selected_device, set_selected_device, clear_selected_device
from managers.device import (
    get_usb_devices,
    ensure_device_connected,
    build_adb_cmd,
)


def select_usb_device_for_wireless():
    """
    Prompt user to select a USB device if multiple are connected.
    Sets the selected device.
    Returns: True if device selected/available, False if no devices
    """
    devices = get_usb_devices()

    if not devices:
        return False

    if len(devices) == 1:
        # Only one USB device, auto-select it
        set_selected_device(devices[0])
        return True

    # Multiple USB devices found, ask user to select
    print(f"\n{YELLOW}Multiple USB devices detected:{NC}")
    for i, device in enumerate(devices, 1):
        print(f"  {i}. {device}")

    print()
    while True:
        try:
            choice = input(f"Select USB device (1-{len(devices)}): ").strip()
            index = int(choice) - 1
            if 0 <= index < len(devices):
                set_selected_device(devices[index])
                print(f"{GREEN}✓ Selected: {devices[index]}{NC}\n")
                return True
            else:
                print(f"{RED}Invalid choice. Please enter a number between 1 and {len(devices)}{NC}")
        except ValueError:
            print(f"{RED}Invalid input. Please enter a number{NC}")
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Selection cancelled{NC}")
            return False


def setup_wireless_adb():
    """
    Setup wireless ADB connection
    Guides user through connecting device wirelessly
    """
    print(f"{YELLOW}Setting up Wireless ADB...{NC}\n")

    # Check if USB device is connected and select it
    if not select_usb_device_for_wireless():
        print(f"{RED}Error: No device connected via USB!{NC}")
        print(f"{YELLOW}Please connect your device via USB first{NC}")
        return False

    selected_device = get_selected_device()
    print(f"{GREEN}✓ Device found: {selected_device}{NC}")
    print(f"\n{BLUE}Step 1: Getting device IP address...{NC}")

    # Get device IP address
    try:
        result = subprocess.run(
            build_adb_cmd(["shell", "ip", "addr", "show", "wlan0"]),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )

        if result.returncode == 0:
            # Extract IP address
            match = PATTERNS['ip_address'].search(result.stdout)
            if match:
                device_ip = match.group(1)
                print(f"{GREEN}Device IP: {device_ip}{NC}")
            else:
                print(f"{RED}Could not detect IP address{NC}")
                device_ip = input(f"Enter device IP address manually: ")
        else:
            device_ip = input(f"Enter device IP address: ")
    except Exception:
        device_ip = input(f"Enter device IP address: ")

    if not device_ip:
        print(f"{RED}IP address required!{NC}")
        return False

    print(f"\n{BLUE}Step 2: Setting up ADB on port 5555...{NC}")
    # Enable TCP/IP mode on port 5555
    result = subprocess.run(
        build_adb_cmd(["tcpip", "5555"]),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    if result.returncode != 0:
        print(f"{RED}Failed to enable TCP/IP mode{NC}")
        print(f"{YELLOW}Error: {result.stderr}{NC}")
        return False

    print(f"{GREEN}✓ TCP/IP mode enabled{NC}")
    print(f"\n{YELLOW}You can now disconnect the USB cable{NC}")
    input("Press Enter after disconnecting USB cable...")

    # Clear selected device since we're switching to wireless
    clear_selected_device()

    print(f"\n{BLUE}Step 3: Connecting to {device_ip}:5555...{NC}")
    # Connect to device wirelessly (don't use device selection for connect command)
    result = subprocess.run(
        ["adb", "connect", f"{device_ip}:5555"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    if result.returncode == 0 and "connected" in result.stdout.lower():
        print(f"{GREEN}✓ Wireless ADB connected successfully!{NC}")
        print(f"\n{BLUE}Device: {device_ip}:5555{NC}")
        print(f"\n{YELLOW}To disconnect: adb disconnect{NC}")
        print(f"{YELLOW}To reconnect via USB: adb usb{NC}")
        return True
    else:
        print(f"{RED}Failed to connect wirelessly{NC}")
        print(f"{YELLOW}Output: {result.stdout}{NC}")
        return False


def launch_scrcpy():
    """
    Launch scrcpy with optimized settings
    """
    print(f"{YELLOW}Launching scrcpy...{NC}\n")

    # Check if scrcpy is installed (cross-platform)
    scrcpy_path = shutil.which("scrcpy")
    if not scrcpy_path:
        print(f"{RED}Error: scrcpy not found!{NC}")
        if is_windows():
            print(f"{YELLOW}Install: scoop install scrcpy  OR  choco install scrcpy{NC}")
        elif is_macos():
            print(f"{YELLOW}Install: brew install scrcpy{NC}")
        else:
            print(f"{YELLOW}Install: sudo apt install scrcpy  OR  sudo snap install scrcpy{NC}")
        return False

    # Check for connected device and select if multiple
    if not ensure_device_connected(
        "No device connected!",
        "Connect device via USB or use 'fdev mirror --wireless' for wireless setup"
    ):
        return False

    selected_device = get_selected_device()
    print(f"{GREEN}✓ Device found: {selected_device}{NC}")

    # Build scrcpy command with optimized settings
    cmd = ["scrcpy", "-s", selected_device, "--no-mouse-hover", "--always-on-top", "-m", "1080", "-b", "5M"]

    print(f"\n{BLUE}Launching scrcpy...{NC}")
    print(f"{YELLOW}Command: {' '.join(cmd)}{NC}\n")

    try:
        # Launch scrcpy (blocking call)
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print(f"\n{GREEN}✓ scrcpy closed successfully{NC}")
            return True
        else:
            print(f"\n{YELLOW}scrcpy exited with code {result.returncode}{NC}")
            return False
    except KeyboardInterrupt:
        print(f"\n{YELLOW}scrcpy interrupted by user{NC}")
        return False
    except Exception as e:
        print(f"{RED}Error launching scrcpy: {e}{NC}")
        return False
