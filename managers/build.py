#!/usr/bin/env python3
"""
Build Manager - APK/AAB build functions
"""

import time
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

from common_utils import (
    RED, GREEN, YELLOW, BLUE, NC, MAGENTA, CHECKMARK, CROSS,
    timer_decorator,
    is_windows,
    open_directory,
)
from core.constants import PATTERNS, PATHS


def show_loading(description, process):
    """
    Displays a loading spinner with a custom message while a process is running
    Parameters:
        description: Description message to display
        process: Process object to monitor
    """
    spinner_index = 0
    braille_spinner_list = '⡿⣟⣯⣷⣾⣽⣻⢿'
    print(description, end='', flush=True)
    # Continue spinning while the process is running
    while process.poll() is None:
        print(f"\b{MAGENTA}{braille_spinner_list[spinner_index]}{NC}", end='', flush=True)
        spinner_index = (spinner_index + 1) % len(braille_spinner_list)
        time.sleep(0.025)
    stdout, stderr = process.communicate()
    # Display success or failure icon based on the process exit status
    if process.returncode == 0:
        print(f"\b{CHECKMARK} ", flush=True)
        return True
    else:
        print(f"\b{CROSS} ", flush=True)
        if stdout:
            print(f"\n{GREEN}Output:\n{stdout}{NC}")
        if stderr:
            print(f"\n{RED}Error Output:\n{stderr}{NC}")
        return False


def run_flutter_command(cmd_list, description):
    """
    Runs a flutter/dart command with a loading spinner.
    Parameters:
        cmd_list: List of command arguments
        description: Description to show with spinner
    """
    # Windows compatibility for shell commands
    shell_needed = (is_windows() and cmd_list[0] in ['timeout', 'start', 'flutter', 'dart']) or cmd_list[0] == 'pod'

    process = subprocess.Popen(
        cmd_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell_needed,
        encoding='utf-8',
        errors='replace'
    )
    return show_loading(description, process)


def get_package_name():
    """
    Dynamically extract package name (applicationId) from Android build files.
    Checks both build.gradle.kts and build.gradle files.
    Returns the package name or None if not found.
    """
    gradle_kts_path = PATHS['gradle_kts']
    gradle_path = PATHS['gradle']

    # Try build.gradle.kts first
    if gradle_kts_path.exists():
        try:
            with open(gradle_kts_path, 'r', encoding='utf-8') as file:
                content = file.read()
                match = PATTERNS['package_name_kts'].search(content)
                if match:
                    return match.group(1)
        except Exception as e:
            print(f"{YELLOW}Warning: Could not read {gradle_kts_path}: {e}{NC}")

    # Try build.gradle (Groovy format)
    if gradle_path.exists():
        try:
            with open(gradle_path, 'r', encoding='utf-8') as file:
                content = file.read()
                match = PATTERNS['package_name_groovy'].search(content)
                if match:
                    return match.group(1)
        except Exception as e:
            print(f"{YELLOW}Warning: Could not read {gradle_path}: {e}{NC}")

    print(f"{RED}Error: Could not find package name in build.gradle or build.gradle.kts{NC}")
    print(f"{YELLOW}Searched in: android/app/build.gradle and android/app/build.gradle.kts{NC}")
    return None


def get_app_label_from_manifest():
    """
    Extract app label from AndroidManifest.xml
    Returns the app label or None if not found
    """
    manifest_path = PATHS['manifest']

    if not manifest_path.exists():
        print(f"{YELLOW}Warning: AndroidManifest.xml not found at {manifest_path}{NC}")
        return None

    try:
        with open(manifest_path, 'r', encoding='utf-8') as file:
            content = file.read()
            match = PATTERNS['app_label'].search(content)
            if match:
                label = match.group(1)
                # If it's a string resource reference, try to get actual value
                if label.startswith('@string/'):
                    return None
                # Decode HTML entities like &amp; to &
                label = label.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                return label
            else:
                print(f"{YELLOW}Warning: Could not find android:label in AndroidManifest.xml{NC}")
                return None
    except Exception as e:
        print(f"{YELLOW}Warning: Could not read AndroidManifest.xml: {e}{NC}")
        return None


def sanitize_filename(name):
    """
    Sanitize app name for use in filename (cross-platform compatible)
    Removes/replaces characters not allowed in Windows/macOS/Linux filenames
    """
    # Replace & with 'and'
    name = name.replace('&', 'and')
    # Remove Windows forbidden characters: < > : " / \ | ? *
    name = PATTERNS['sanitize_special'].sub('', name)
    # Remove any remaining special characters except alphanumeric, spaces, hyphens, underscores
    name = PATTERNS['sanitize_non_word'].sub('', name)
    # Replace multiple spaces/hyphens with single underscore
    name = PATTERNS['sanitize_spaces'].sub('_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name


def get_formatted_date():
    """
    Get current date formatted as 'DD_MMM' (e.g., '07_Jan')
    """
    return datetime.now().strftime('%d_%b')


def rename_build_files(output_dir, file_extension, app_label=None):
    """
    Rename APK/AAB files with app label and date
    Parameters:
        output_dir: Directory containing the build files (Path object)
        file_extension: File extension to search for ('apk' or 'aab')
        app_label: Optional app label (if None, will extract from AndroidManifest.xml)
    """
    if not output_dir.exists():
        print(f"{YELLOW}Warning: Output directory {output_dir} does not exist{NC}")
        return

    # Get app label from AndroidManifest.xml if not provided
    if app_label is None:
        app_label = get_app_label_from_manifest()

    if not app_label:
        print(f"{YELLOW}Warning: Could not get app label, files will not be renamed{NC}")
        return

    # Sanitize app name for filename
    sanitized_name = sanitize_filename(app_label)

    # Get formatted date
    date_str = get_formatted_date()

    # Find all files with the specified extension
    build_files = list(output_dir.glob(f"*.{file_extension}"))

    if not build_files:
        print(f"{YELLOW}Warning: No {file_extension.upper()} files found in {output_dir}{NC}")
        return

    print(f"\n{BLUE}Renaming {file_extension.upper()} files...{NC}")

    for file_path in build_files:
        # Check if file contains architecture info (e.g., arm64-v8a)
        arch_match = PATTERNS['architecture'].search(file_path.name)

        if arch_match:
            # Include architecture in filename
            arch = arch_match.group(1)
            new_name = f"{sanitized_name}_{arch}_{date_str}.{file_extension}"
        else:
            # No architecture info
            new_name = f"{sanitized_name}_{date_str}.{file_extension}"

        new_path = output_dir / new_name

        # Rename the file
        try:
            shutil.move(str(file_path), str(new_path))
            print(f"{GREEN}  ✓ Renamed: {file_path.name} → {new_name}{NC}")
        except Exception as e:
            print(f"{RED}  ✗ Failed to rename {file_path.name}: {e}{NC}")


def display_build_size(file_type, directory):
    """
    Display build file size (works for both APK and AAB)

    Parameters:
        file_type: "apk" or "aab"
        directory: Path object or string of the directory containing build files

    Returns:
        None
    """
    # Convert to Path object if string
    build_dir = Path(directory) if isinstance(directory, str) else directory

    # Get files with the specified extension
    build_files = list(build_dir.glob(f"*.{file_type}")) if build_dir.exists() else []

    if build_files:
        for build_file in build_files:
            size_bytes = build_file.stat().st_size
            size_mb = round(size_bytes / 1048576, 2)
            # Display with uppercase file type (APK, AAB)
            print(f"{BLUE}{file_type.upper()}: {build_file.name} | Size: {size_mb} MB{NC}")
    else:
        print(f"{RED}{file_type.upper()} file not found in {build_dir}{NC}")


def common_build_process(
    build_name,
    build_command,
    build_description,
    output_dir,
    file_extension,
    install_after=False
):
    """
    Common build process for all build types (APK, APK-split, AAB)

    Parameters:
        build_name: Display name for the build (e.g., "APK", "AAB")
        build_command: List of flutter build command arguments
        build_description: Loading text for the build step
        output_dir: Path object where build output is located
        file_extension: "apk" or "aab"
        install_after: Boolean to install APK after build (default: False)

    Returns:
        Boolean indicating success
    """
    # Initial message
    print(f"{YELLOW}Building {build_name}...{NC}\n")

    # Step 1: Clean the project
    run_flutter_command(["flutter", "clean"], "Cleaning project...                                   ")

    # Step 2: Get dependencies
    run_flutter_command(["flutter", "pub", "get"], "Getting dependencies...                              ")

    # Step 3: Generate localizations
    run_flutter_command(["flutter", "gen-l10n"], "Generating localizations...                          ")

    # Step 4: Generate build files
    run_flutter_command(["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"], "Generating build files...                            ")

    # Step 5: Build (APK/AAB)
    run_flutter_command(build_command, build_description)

    # Step 6: Rename build files with app label and date
    rename_build_files(output_dir, file_extension)

    # Step 7: Display file size
    display_build_size(file_extension, output_dir)

    # Step 8: Install (if requested) or open directory
    if install_after:
        # Import here to avoid circular imports
        from managers.app import install_apk
        install_result = install_apk()
        if install_result:
            print(f"\n{GREEN}✓ {build_name} built and installed successfully!{NC}")
        else:
            print(f"\n{RED}✗ {build_name} built but install failed!{NC}")
        return install_result
    else:
        # Success message
        print(f"\n{GREEN}✓ {build_name} built successfully!{NC}")
        # Open the directory containing the build
        open_directory(str(output_dir))
        return True


@timer_decorator
def build_apk():
    """Build APK (Full Process)"""
    return common_build_process(
        build_name="APK (Full Process)",
        build_command=[
            "flutter", "build", "apk", "--release", "--obfuscate",
            "--target-platform", "android-arm64", "--split-debug-info=./"
        ],
        build_description="Building APK...                                      ",
        output_dir=PATHS['apk_output'],
        file_extension="apk",
        install_after=False
    )


@timer_decorator
def build_apk_split_per_abi():
    """Build APK with --split-per-abi"""
    return common_build_process(
        build_name="APK (split-per-abi)",
        build_command=[
            "flutter", "build", "apk", "--release", "--split-per-abi",
            "--obfuscate", "--split-debug-info=./"
        ],
        build_description="Building APK (split-per-abi)...                      ",
        output_dir=PATHS['apk_output'],
        file_extension="apk",
        install_after=False
    )


@timer_decorator
def build_aab():
    """Build AAB"""
    return common_build_process(
        build_name="AAB",
        build_command=[
            "flutter", "build", "appbundle", "--release",
            "--obfuscate", "--split-debug-info=./"
        ],
        build_description="Building AAB...                                      ",
        output_dir=PATHS['aab_output'],
        file_extension="aab",
        install_after=False
    )


@timer_decorator
def release_run():
    """Build & Install Release APK"""
    return common_build_process(
        build_name="Release APK",
        build_command=[
            "flutter", "build", "apk", "--release", "--obfuscate",
            "--target-platform", "android-arm64", "--split-debug-info=./"
        ],
        build_description="Building APK...                                      ",
        output_dir=PATHS['apk_output'],
        file_extension="apk",
        install_after=True
    )
