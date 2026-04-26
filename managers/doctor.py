#!/usr/bin/env python3
"""
Doctor Module - Environment health check for Flutter development
Checks all required and optional tools, dependencies, and configurations
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

from common_utils import RED, GREEN, YELLOW, BLUE, NC, CHECKMARK, CROSS, is_macos, is_windows


def _get_cmd_version(cmd_list, timeout=5):
    """
    Run a command and return its output (first line).
    Returns None if the command is not found or fails.
    """
    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace',
        )
        output = result.stdout.strip() or result.stderr.strip()
        if result.returncode == 0 and output:
            return output.splitlines()[0]
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _extract_version(raw, prefix=None):
    """Extract version number from a raw version string."""
    if not raw:
        return None
    if prefix:
        raw = raw.replace(prefix, '').strip()
    # Take first token that looks like a version
    import re
    match = re.search(r'[\d]+(?:\.[\d]+)*', raw)
    return match.group(0) if match else raw.strip()


def _check_tool(name, cmd_list, required=True, install_hint=None, version_prefix=None):
    """
    Check if a tool is installed and return (status, version_str, name).
    status: True = found, False = not found
    """
    raw = _get_cmd_version(cmd_list)
    if raw:
        version = _extract_version(raw, version_prefix)
        return True, version
    else:
        return False, install_hint


def _check_python_package(package_name):
    """Check if a Python package is installed and return its version."""
    try:
        mod = __import__(package_name.replace('-', '_'))
        version = getattr(mod, '__version__', None) or getattr(mod, 'VERSION', 'installed')
        return True, str(version)
    except ImportError:
        return False, f"pip install {package_name}"


def _check_env_file():
    """Check .env file existence and API key configuration."""
    script_dir = Path(__file__).parent.parent
    env_path = script_dir / '.env'

    if not env_path.exists():
        return False, ".env file not found"

    # Read and check for configured API keys
    configured_keys = []
    default_service = None

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            if key == 'DEFAULT_AI_SERVICE' and value:
                default_service = value

            # Check if API key is actually set (not placeholder)
            if key.endswith('_API_KEY') and value and 'your_' not in value.lower() and 'here' not in value.lower():
                service = key.replace('_API_KEY', '').lower()
                configured_keys.append(service)

    if configured_keys:
        active = default_service or configured_keys[0]
        return True, f"active: {active} ({len(configured_keys)} key(s) configured)"
    else:
        return False, "no API keys configured"


def _check_flutter_project():
    """Check if current directory is a Flutter project."""
    pubspec = Path('pubspec.yaml')
    if pubspec.exists():
        # Try to extract project name
        try:
            with open(pubspec, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('name:'):
                        name = line.split(':', 1)[1].strip()
                        return True, name
        except Exception:
            pass
        return True, "detected"
    return False, "not a Flutter project directory"


def run_doctor():
    """Run full environment health check."""
    print(f"\n{BLUE}╔══════════════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║          fdev doctor - Environment Health Check      ║{NC}")
    print(f"{BLUE}╚══════════════════════════════════════════════════════╝{NC}")
    print(f"{BLUE}Platform: {GREEN}{platform.system()} {platform.machine()}{NC}")
    print(f"{BLUE}Python:   {GREEN}{platform.python_version()} ({sys.executable}){NC}")
    print()

    passed = 0
    failed = 0
    warnings = 0

    def print_result(name, status, detail, required=True, pad=22):
        nonlocal passed, failed, warnings
        label = name.ljust(pad)
        if status:
            print(f"  {CHECKMARK}  {label} {GREEN}{detail}{NC}")
            passed += 1
        elif required:
            print(f"  {CROSS}  {label} {RED}{detail}{NC}")
            failed += 1
        else:
            print(f"  {YELLOW}!{NC}  {label} {YELLOW}{detail}{NC}")
            warnings += 1

    # ── Core Tools (Required) ──────────────────────────────
    print(f"{BLUE}Core Tools (required):{NC}")

    status, detail = _check_tool("Flutter", ["flutter", "--version"], version_prefix="Flutter")
    print_result("Flutter SDK", status, detail)

    status, detail = _check_tool("Dart", ["dart", "--version"], version_prefix="Dart SDK version:")
    print_result("Dart SDK", status, detail)

    status, detail = _check_tool("Git", ["git", "--version"], version_prefix="git version")
    print_result("Git", status, detail)

    # Python packages
    status, detail = _check_python_package("dotenv")
    print_result("python-dotenv", status, detail)

    status, detail = _check_python_package("requests")
    print_result("requests", status, detail)

    # ── Android Tools ──────────────────────────────────────
    print(f"\n{BLUE}Android Tools:{NC}")

    status, detail = _check_tool("ADB", ["adb", "--version"])
    if status and detail:
        detail = _extract_version(detail)
    print_result("ADB", status, detail or "not found (install Android SDK platform-tools)", required=False)

    # Check Java/JDK (needed for Android builds)
    status, detail = _check_tool("Java", ["java", "-version"])
    if not status:
        detail = "not found (install JDK for Android builds)"
    print_result("Java/JDK", status, detail, required=False)

    # Check connected devices
    if shutil.which("adb"):
        try:
            result = subprocess.run(
                ["adb", "devices"], capture_output=True, text=True, timeout=5
            )
            lines = [l for l in result.stdout.strip().splitlines()[1:] if l.strip() and 'device' in l]
            if lines:
                print_result("Connected Devices", True, f"{len(lines)} device(s) connected", required=False)
            else:
                print_result("Connected Devices", False, "no devices connected", required=False)
        except Exception:
            print_result("Connected Devices", False, "could not check", required=False)

    # ── iOS Tools (macOS only) ─────────────────────────────
    if is_macos():
        print(f"\n{BLUE}iOS Tools (macOS):{NC}")

        status, detail = _check_tool("Xcode", ["xcodebuild", "-version"])
        print_result("Xcode", status, detail or "not found (install from App Store)", required=False)

        status, detail = _check_tool("CocoaPods", ["pod", "--version"])
        print_result("CocoaPods", status, detail or "not found (gem install cocoapods)", required=False)

        # xcrun check
        status, detail = _check_tool("xcrun", ["xcrun", "--version"])
        if status and detail:
            detail = _extract_version(detail)
        print_result("xcrun", status, detail or "not found (install Xcode CLI tools)", required=False)

    # ── Optional Tools ─────────────────────────────────────
    print(f"\n{BLUE}Optional Tools:{NC}")

    status, detail = _check_tool("scrcpy", ["scrcpy", "--version"])
    if not status:
        if is_macos():
            detail = "not found (brew install scrcpy)"
        elif is_windows():
            detail = "not found (scoop install scrcpy)"
        else:
            detail = "not found (apt install scrcpy)"
    print_result("scrcpy", status, detail, required=False)

    status, detail = _check_tool("Firebase CLI", ["firebase", "--version"])
    if not status:
        detail = "not found (npm install -g firebase-tools)"
    print_result("Firebase CLI", status, detail, required=False)

    # VSCode CLI
    status, detail = _check_tool("VSCode", ["code", "--version"])
    if status and detail:
        detail = detail.splitlines()[0]
    if not status:
        detail = "not found (install VSCode + shell command)"
    print_result("VSCode CLI", status, detail, required=False)

    # ── Configuration ──────────────────────────────────────
    print(f"\n{BLUE}Configuration:{NC}")

    status, detail = _check_env_file()
    print_result(".env File", status, detail)

    status, detail = _check_flutter_project()
    print_result("Flutter Project", status, detail, required=False)

    # Check if fdev is globally accessible
    fdev_path = shutil.which("fdev")
    if fdev_path:
        print_result("fdev Global", True, fdev_path, required=False)
    else:
        print_result("fdev Global", False, "not in PATH (run setup.py)", required=False)

    # ── Summary ────────────────────────────────────────────
    print(f"\n{BLUE}{'─' * 54}{NC}")
    total = passed + failed + warnings
    summary_parts = []
    if passed:
        summary_parts.append(f"{GREEN}{passed} passed{NC}")
    if warnings:
        summary_parts.append(f"{YELLOW}{warnings} warning(s){NC}")
    if failed:
        summary_parts.append(f"{RED}{failed} issue(s){NC}")
    print(f"  {' | '.join(summary_parts)}  (total: {total} checks)")

    if failed == 0:
        print(f"\n  {GREEN}All required tools are installed! Happy coding!{NC}")
    else:
        print(f"\n  {YELLOW}Fix the issues above to get full fdev functionality.{NC}")

    print()
