#!/usr/bin/env python3
"""
DateTime Manager - Open device Date & Time settings with auto-time disabled
"""

import subprocess

from common_utils import RED, GREEN, YELLOW, BLUE, NC
from core.state import get_selected_device
from managers.device import ensure_device_connected, build_adb_cmd


def _run_adb(args, timeout=5):
    return subprocess.run(
        build_adb_cmd(args),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=timeout,
    )


def open_datetime_settings():
    """Disable auto-time and open Date & Time settings on the device."""
    if not ensure_device_connected(
        "No device connected!",
        "Connect a device via USB or use 'fdev mirror --wireless' first",
    ):
        return False

    print(f"{GREEN}✓ Device: {get_selected_device()}{NC}")

    print(f"{BLUE}Disabling automatic date & time...{NC}")
    result = _run_adb(["shell", "settings put global auto_time 0"])
    if result.returncode != 0:
        print(f"{RED}✗ Failed to disable auto-time{NC}")
        print(f"{YELLOW}{result.stderr.strip()}{NC}")
        return False
    print(f"{GREEN}✓ Auto-time disabled{NC}")

    print(f"{BLUE}Opening Date & Time settings on device...{NC}")
    result = _run_adb(["shell", "am start -a android.settings.DATE_SETTINGS"])
    if result.returncode != 0:
        print(f"{RED}✗ Failed to open settings{NC}")
        return False

    print(f"{GREEN}✓ Settings opened — set the date/time manually on device{NC}")
    return True
