#!/usr/bin/env python3
"""
Device Manager - Device selection and ADB commands
"""

import subprocess

from common_utils import RED, GREEN, YELLOW, BLUE, NC
from core.state import get_selected_device, set_selected_device


def get_device_model(serial):
    """
    Get the device model name for a given device serial.
    Returns: Model name string or empty string if failed
    """
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "shell", "getprop", "ro.product.model"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=3
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def get_all_connected_devices():
    """
    Get all connected Android devices/emulators
    Returns: List of device serials, or empty list if none found
    """
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )

        if result.returncode == 0:
            devices = []
            lines = result.stdout.strip().split('\n')
            # Skip the first line ("List of devices attached")
            for line in lines[1:]:
                if line.strip() and '\tdevice' in line:
                    # Extract device serial (first part before tab)
                    serial = line.split('\t')[0].strip()
                    devices.append(serial)
            return devices
        return []
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def select_device_if_multiple():
    """
    Check for connected devices and prompt user to select if multiple found.
    Sets the global SELECTED_DEVICE variable.
    Returns: True if device selected/available, False if no devices
    """
    devices = get_all_connected_devices()

    if not devices:
        return False

    if len(devices) == 1:
        # Only one device, auto-select it
        set_selected_device(devices[0])
        return True

    # Multiple devices found, ask user to select
    print(f"\n{YELLOW}Multiple devices detected:{NC}")
    for i, device in enumerate(devices, 1):
        model = get_device_model(device)
        model_str = f" {model}" if model else ""
        # Check if it's a network device
        if ':' in device:
            print(f"  {i}.{model_str} {device} {BLUE}(wireless){NC}")
        else:
            print(f"  {i}.{model_str} {device} {GREEN}(USB){NC}")

    print()
    while True:
        try:
            choice = input(f"Select device (1-{len(devices)}): ").strip()
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


def build_adb_cmd(cmd_list, require_device=True):
    """
    Build ADB command with device selection if needed.
    Parameters:
        cmd_list: List of command parts (e.g., ["shell", "pm", "clear", "package"])
        require_device: If True, adds -s flag when SELECTED_DEVICE is set
    Returns: Complete command list ready for subprocess
    """
    selected_device = get_selected_device()

    # Start with "adb"
    adb_cmd = ["adb"]

    # Add device selection if needed
    if require_device and selected_device:
        adb_cmd.extend(["-s", selected_device])

    # Add the rest of the command
    adb_cmd.extend(cmd_list)

    return adb_cmd


def ensure_device_connected(error_message=None, additional_help=None):
    """
    Wrapper function to check and select Android device

    Parameters:
        error_message: Custom error message (default: "No Android device connected!")
        additional_help: Additional help text to display after error

    Returns:
        Boolean - True if device selected/available, False otherwise
    """
    if not select_device_if_multiple():
        # Use custom error message or default
        if error_message:
            print(f"{RED}Error: {error_message}{NC}")
        else:
            print(f"{RED}Error: No Android device connected!{NC}")

        # Display additional help if provided
        if additional_help:
            print(f"{YELLOW}{additional_help}{NC}")

        return False

    return True


def get_usb_devices():
    """
    Get only USB connected devices (excludes wireless/network devices)
    Returns: List of USB device serials
    """
    all_devices = get_all_connected_devices()
    # Filter out wireless devices (they contain ':' in serial like '192.168.0.131:5555')
    usb_devices = [d for d in all_devices if ':' not in d]
    return usb_devices


def select_usb_device():
    """
    Prompt user to select a USB device if multiple are connected.
    Sets the global SELECTED_DEVICE variable.
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
        model = get_device_model(device)
        model_str = f" {model}" if model else ""
        print(f"  {i}.{model_str} {device} {GREEN}(USB){NC}")

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
