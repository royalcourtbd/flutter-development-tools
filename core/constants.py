#!/usr/bin/env python3
"""
Constants and compiled regex patterns
"""
import re
from pathlib import Path

# Regex patterns (compiled once)
PATTERNS = {
    'package_name_kts': re.compile(r'applicationId\s*=\s*["\']([^"\']+)["\']'),
    'package_name_groovy': re.compile(r'applicationId\s+["\']([^"\']+)["\']'),
    'app_label': re.compile(r'android:label="([^"]+)"'),
    'architecture': re.compile(r'(arm64-v8a|armeabi-v7a|x86|x86_64)'),
    'version': re.compile(r'^version:\s*(.+)$', re.MULTILINE),
    'version_with_build': re.compile(r'^version:\s*["\']?([\d\.]+)\+(\d+)["\']?', re.MULTILINE),
    'version_line': re.compile(r'^version:\s*["\']?[\d\.]+(\+\d+)?["\']?', re.MULTILINE),
    'ip_address': re.compile(r'inet (\d+\.\d+\.\d+\.\d+)'),
    'foreground_app': re.compile(r'u0 ([^/\s]+)'),
    'resumed_activity': re.compile(r'mResumedActivity.*?{.*?u0\s+(\S+?)/'),
    'top_resumed_activity': re.compile(r'(?:top)?ResumedActivity.*?u0\s+(\S+?)/'),
    'sanitize_special': re.compile(r'[<>:"/\\|?*]'),
    'sanitize_non_word': re.compile(r'[^\w\s-]'),
    'sanitize_spaces': re.compile(r'[-\s]+'),
}

# Path constants
PATHS = {
    'gradle_kts': Path("android/app/build.gradle.kts"),
    'gradle': Path("android/app/build.gradle"),
    'manifest': Path("android/app/src/main/AndroidManifest.xml"),
    'pubspec': Path("pubspec.yaml"),
    'info_plist': Path("ios/Runner/Info.plist"),
    'apk_output': Path("build/app/outputs/flutter-apk"),
    'aab_output': Path("build/app/outputs/bundle/release"),
}

# Build commands
BUILD_COMMANDS = {
    'apk': [
        "flutter", "build", "apk", "--release", "--obfuscate",
        "--target-platform", "android-arm64", "--split-debug-info=./"
    ],
    'apk_split': [
        "flutter", "build", "apk", "--release", "--split-per-abi",
        "--obfuscate", "--split-debug-info=./"
    ],
    'aab': [
        "flutter", "build", "appbundle", "--release",
        "--obfuscate", "--split-debug-info=./"
    ],
}
