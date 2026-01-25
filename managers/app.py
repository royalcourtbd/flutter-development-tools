#!/usr/bin/env python3
"""
App Manager - Install, uninstall, clear data functions
"""

import subprocess

from common_utils import RED, GREEN, YELLOW, BLUE, NC
from core.constants import PATTERNS, PATHS
from managers.device import (
    get_all_connected_devices,
    ensure_device_connected,
    build_adb_cmd,
)
from managers.build import run_flutter_command, get_package_name


def is_flutter_project_root():
    """
    Check if current directory is a Flutter project root.
    Returns True if pubspec.yaml exists in current directory.
    """
    return PATHS['pubspec'].exists()


def is_app_installed(package_name):
    """
    Check if an app with the given package name is installed on the Android device.
    Uses 'adb shell pm path' which returns the APK path if installed, empty if not.

    Returns: True if installed, False otherwise
    """
    try:
        result = subprocess.run(
            build_adb_cmd(["shell", "pm", "path", package_name]),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        # If app is installed, output will be like: "package:/data/app/..."
        # If not installed, output will be empty or error
        return result.returncode == 0 and result.stdout.strip().startswith("package:")
    except (subprocess.TimeoutExpired, Exception):
        return False


def get_current_foreground_app():
    """
    Get the package name of currently running foreground app
    Returns: (platform, package_name) tuple or (None, None) if failed
    """
    # Check for iOS simulator first
    try:
        ios_check = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "booted"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        ios_connected = ios_check.returncode == 0 and "Booted" in ios_check.stdout

        if ios_connected:
            # Get foreground app on iOS simulator
            result = subprocess.run(
                ["xcrun", "simctl", "spawn", "booted", "launchctl", "list"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )

            if result.returncode == 0:
                # Get frontmost app using AppleScript (macOS only)
                applescript = '''tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    return frontApp
                end tell'''

                try:
                    front_result = subprocess.run(
                        ["osascript", "-e", applescript],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=3
                    )

                    if front_result.returncode == 0:
                        app_name = front_result.stdout.strip()
                        if app_name and app_name.lower() == "simulator":
                            # Try to get bundle ID from iOS simulator
                            # For now, return a placeholder - iOS doesn't easily expose current app
                            print(f"{YELLOW}iOS Simulator is running but cannot automatically detect current app{NC}")
                            print(f"{YELLOW}Please use 'fdev uninstall' to manually uninstall{NC}")
                            return ("ios", None)
                except Exception:
                    pass

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check for Android device
    try:
        devices = get_all_connected_devices()
        android_connected = len(devices) > 0

        if android_connected:
            # Select device if multiple connected
            if not ensure_device_connected():
                return (None, None)

            # Get current foreground app on Android
            result = subprocess.run(
                build_adb_cmd(["shell", "dumpsys", "window", "windows"]),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )

            if result.returncode == 0:
                # Parse output to find current focused app
                for line in result.stdout.split('\n'):
                    if 'mCurrentFocus' in line or 'mFocusedApp' in line or 'mFocusedWindow' in line:
                        # Extract package name using regex
                        match = PATTERNS['foreground_app'].search(line)
                        if match:
                            package_name = match.group(1)
                            return ("android", package_name)

                # Fallback: Try using dumpsys activity
                result2 = subprocess.run(
                    build_adb_cmd(["shell", "dumpsys", "activity", "activities"]),
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=5
                )

                if result2.returncode == 0:
                    # Try multiple patterns for different Android versions
                    # Pattern 1: mResumedActivity (older Android)
                    match = PATTERNS['resumed_activity'].search(result2.stdout)
                    if match:
                        package_name = match.group(1)
                        return ("android", package_name)

                    # Pattern 2: topResumedActivity or ResumedActivity (newer Android)
                    match = PATTERNS['top_resumed_activity'].search(result2.stdout)
                    if match:
                        package_name = match.group(1)
                        return ("android", package_name)

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return (None, None)


def clear_app_data():
    """
    Automatically clear data of currently running foreground app
    Works for both Android and iOS on all operating systems (macOS, Linux, Windows)
    """
    print(f"{YELLOW}Clearing app data for foreground app...{NC}\n")

    # Get current foreground app
    platform_type, package_name = get_current_foreground_app()

    if not platform_type:
        print(f"{RED}Error: No device/simulator detected!{NC}")
        print(f"{YELLOW}Please connect an Android device or start an iOS simulator{NC}")
        return False

    if not package_name:
        print(f"{RED}Error: Could not detect foreground app{NC}")
        print(f"{YELLOW}Make sure an app is running in the foreground{NC}")
        return False

    print(f"{BLUE}Platform: {platform_type.upper()}{NC}")
    print(f"{BLUE}App: {package_name}{NC}\n")

    # Ask for confirmation
    user_input = input(f"Clear data for {GREEN}{package_name}{NC}? (Y/n): ")
    if user_input.lower() == 'n':
        print(f"{YELLOW}Operation cancelled{NC}")
        return False

    # Clear data based on platform
    if platform_type == "android":
        # Clear app data on Android
        success = run_flutter_command(
            build_adb_cmd(["shell", "pm", "clear", package_name]),
            f"Clearing app data...                                "
        )

        if success:
            print(f"\n{GREEN}✓ App data cleared successfully!{NC}")
            print(f"{BLUE}You can now relaunch the app from the device{NC}")
        else:
            print(f"\n{RED}✗ Failed to clear app data!{NC}")
            print(f"{YELLOW}Make sure the app package name is correct{NC}")

        return success

    elif platform_type == "ios":
        # iOS doesn't support direct app data clearing via command line
        # We need to uninstall and reinstall the app
        print(f"{YELLOW}iOS Note: iOS doesn't support clearing app data directly{NC}")
        print(f"{YELLOW}Options:{NC}")
        print(f"{BLUE}  1. Reset app data from device: Settings → General → iPhone Storage → [App] → Delete App{NC}")
        print(f"{BLUE}  2. Uninstall and reinstall the app using 'fdev uninstall' then 'fdev install'{NC}")
        print(f"{BLUE}  3. On simulator: Device → Erase All Content and Settings{NC}")

        # Offer to uninstall
        user_choice = input(f"\nWould you like to uninstall the app instead? (y/N): ")
        if user_choice.lower() == 'y':
            return uninstall_app()

        return False

    return False


def _uninstall_from_project_root():
    """
    Uninstall app using project files (build.gradle / Info.plist).
    Called when running from Flutter project root directory.
    """
    # Check which device is connected
    try:
        ios_check = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "booted"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        ios_connected = ios_check.returncode == 0 and "Booted" in ios_check.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        ios_connected = False

    devices = get_all_connected_devices()
    android_connected = len(devices) > 0

    # Handle iOS Simulator
    if ios_connected and not android_connected:
        print(f"{BLUE}iOS Simulator detected{NC}")

        info_plist_path = PATHS['info_plist']
        if not info_plist_path.exists():
            print(f"{RED}Error: Info.plist not found{NC}")
            return False

        try:
            result = subprocess.run(
                ["/usr/libexec/PlistBuddy", "-c", "Print CFBundleIdentifier", str(info_plist_path)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=True
            )
            bundle_id = result.stdout.strip()

            if not bundle_id or bundle_id.startswith("$("):
                bundle_id = get_package_name()
                if not bundle_id:
                    print(f"{RED}Cannot get bundle identifier{NC}")
                    return False

            print(f"{BLUE}Bundle ID: {bundle_id}{NC}")

            success = run_flutter_command(
                ["xcrun", "simctl", "uninstall", "booted", bundle_id],
                "Uninstalling from iOS simulator...                  "
            )

            if success:
                print(f"\n{GREEN}✓ App uninstalled successfully from iOS!{NC}")
            else:
                print(f"\n{RED}✗ Failed to uninstall app from iOS!{NC}")
            return success

        except subprocess.CalledProcessError as e:
            print(f"{RED}Error getting bundle identifier: {e}{NC}")
            return False

    # Handle Android Device
    elif android_connected:
        print(f"{BLUE}Android device detected{NC}")

        if not ensure_device_connected("Device selection failed!"):
            return False

        package_name = get_package_name()
        if not package_name:
            print(f"{RED}Cannot proceed without package name{NC}")
            return False

        print(f"{BLUE}Package name: {package_name}{NC}")

        # Check if the app is installed on the device
        if is_app_installed(package_name):
            print(f"{GREEN}✓ App is installed on device{NC}\n")
            success = run_flutter_command(
                build_adb_cmd(["uninstall", package_name]),
                "Uninstalling from Android...                        "
            )

            if success:
                print(f"\n{GREEN}✓ App uninstalled successfully from Android!{NC}")
            else:
                print(f"\n{RED}✗ Failed to uninstall app from Android!{NC}")
            return success
        else:
            # App not installed - detect and uninstall foreground app instead
            print(f"{YELLOW}⚠️  App is NOT installed on device{NC}")
            print(f"{YELLOW}   Detecting foreground app instead...{NC}\n")

            _, foreground_package = get_current_foreground_app()

            if not foreground_package:
                print(f"{RED}Error: Could not detect foreground app{NC}")
                print(f"{YELLOW}Make sure an app is running in the foreground{NC}")
                return False

            print(f"{BLUE}Foreground App: {foreground_package}{NC}\n")

            # Ask for confirmation before uninstalling foreground app
            print(f"{RED}⚠️  WARNING: This will UNINSTALL the foreground app!{NC}")
            user_input = input(f"Uninstall {GREEN}{foreground_package}{NC}? (Y/n): ")
            if user_input.lower() == 'n':
                print(f"{YELLOW}Operation cancelled{NC}")
                return False

            success = run_flutter_command(
                build_adb_cmd(["uninstall", foreground_package]),
                "Uninstalling foreground app...                      "
            )

            if success:
                print(f"\n{GREEN}✓ Foreground app uninstalled successfully!{NC}")
            else:
                print(f"\n{RED}✗ Failed to uninstall foreground app!{NC}")
            return success

    else:
        print(f"{RED}No device/simulator detected!{NC}")
        print(f"{YELLOW}Please connect an Android device or start an iOS simulator{NC}")
        return False


def _uninstall_foreground_app():
    """
    Uninstall the currently running foreground app.
    Called when NOT in Flutter project root directory.
    Shows extra warnings and requires confirmation.
    """
    print(f"{YELLOW}⚠️  Not in Flutter project directory{NC}")
    print(f"{YELLOW}   Detecting foreground app instead...{NC}\n")

    # Get current foreground app
    platform_type, package_name = get_current_foreground_app()

    if not platform_type:
        print(f"{RED}Error: No device/simulator detected!{NC}")
        print(f"{YELLOW}Please connect an Android device or start an iOS simulator{NC}")
        return False

    if not package_name:
        print(f"{RED}Error: Could not detect foreground app{NC}")
        print(f"{YELLOW}Make sure an app is running in the foreground{NC}")
        return False

    # Show app info with warning
    print(f"{BLUE}Platform: {platform_type.upper()}{NC}")
    print(f"{BLUE}Detected App: {package_name}{NC}\n")

    # Extra warning for foreground app uninstall
    print(f"{RED}⚠️  WARNING: This will UNINSTALL the app completely!{NC}")
    print(f"{RED}   All app data will be permanently deleted.{NC}\n")

    # Simple Y/n confirmation
    user_input = input(f"Uninstall {GREEN}{package_name}{NC}? (Y/n): ")
    if user_input.lower() == 'n':
        print(f"{YELLOW}Operation cancelled{NC}")
        return False

    # Proceed with uninstall
    if platform_type == "android":
        success = run_flutter_command(
            build_adb_cmd(["uninstall", package_name]),
            "Uninstalling from Android...                        "
        )

        if success:
            print(f"\n{GREEN}✓ App uninstalled successfully from Android!{NC}")
        else:
            print(f"\n{RED}✗ Failed to uninstall app from Android!{NC}")
        return success

    elif platform_type == "ios":
        success = run_flutter_command(
            ["xcrun", "simctl", "uninstall", "booted", package_name],
            "Uninstalling from iOS simulator...                  "
        )

        if success:
            print(f"\n{GREEN}✓ App uninstalled successfully from iOS!{NC}")
        else:
            print(f"\n{RED}✗ Failed to uninstall app from iOS!{NC}")
        return success

    return False


def uninstall_app():
    """
    Uninstall the app from connected device (Android/iOS).

    If running from Flutter project root: uses build.gradle/Info.plist for package name.
    If NOT in project root: detects foreground app with extra safety confirmation.
    """
    print(f"{YELLOW}Uninstalling app from device...{NC}\n")

    # Check if we're in a Flutter project root
    if is_flutter_project_root():
        print(f"{GREEN}✓ Flutter project detected{NC}\n")
        return _uninstall_from_project_root()
    else:
        return _uninstall_foreground_app()


def install_apk():
    """
    Installs the built APK on a connected Android device using adb.
    Tries to install arm64-v8a APK first if available.
    Handles signature mismatch by uninstalling existing app first.
    Automatically launches the app after successful installation.
    """
    # Select device if multiple connected
    if not ensure_device_connected():
        return False

    apk_dir = PATHS['apk_output']
    apk_files = [str(f) for f in apk_dir.glob("*.apk")] if apk_dir.exists() else []
    if not apk_files:
        print(f"{RED}No APK found to install!{NC}")
        return False

    # Try to install arm64-v8a APK first, otherwise use the first apk
    target_apk = None
    for apk_path in apk_files:
        if "arm64-v8a" in apk_path:
            target_apk = apk_path
            break
    if not target_apk:
        target_apk = apk_files[0]

    print(f"{YELLOW}Installing {target_apk}...{NC}")

    # First try normal install
    success = run_flutter_command(build_adb_cmd(["install", "-r", target_apk]), "Installing on device...                              ")

    if not success:
        # Get package name dynamically
        package_name = get_package_name()
        if not package_name:
            print(f"{RED}Cannot proceed without package name{NC}")
            return False

        print(f"{YELLOW}Installation failed, trying to uninstall existing app first...{NC}")
        print(f"{BLUE}Package name: {package_name}{NC}")

        # Try to uninstall existing app first using dynamic package name
        run_flutter_command(build_adb_cmd(["uninstall", package_name]), "Uninstalling existing app...                        ")
        # Then try to install again
        success = run_flutter_command(build_adb_cmd(["install", target_apk]), "Reinstalling on device...                           ")

    # Launch app after successful installation
    if success:
        package_name = get_package_name()
        if package_name:
            print(f"{YELLOW}Launching app...{NC}")
            # Launch the app using monkey command (works on all devices)
            launch_success = run_flutter_command(
                build_adb_cmd(["shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"]),
                "Starting app on device...                           "
            )
            if launch_success:
                print(f"{GREEN}✓ App launched successfully!{NC}")
            else:
                print(f"{YELLOW}App installed but failed to launch. Please open manually.{NC}")
        else:
            print(f"{YELLOW}App installed but package name not found for launching.{NC}")

    return success
