#!/usr/bin/env python3
import os
import sys
import time
import signal
import subprocess
import re
import shutil
from pathlib import Path
from datetime import datetime

# Import common utilities
from common_utils import (
    RED, GREEN, YELLOW, BLUE, NC, MAGENTA, CHECKMARK, CROSS,
    timer_decorator,
    is_windows, is_macos, is_linux,
    open_directory
)

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
        # Nicher ei stdout statement ta comment out korle r command er out put dekha jabe na.
        # if stdout:
        #     print(f"\n{GREEN}Output:\n{stdout}{NC}")
        return True
    else:
        print(f"\b{CROSS} ", flush=True)
        # Nicher ei stdout statement ta comment out korle r command er out put dekha jabe na.
        if stdout:
            print(f"\n{GREEN}Output:\n{stdout}{NC}")
        if stderr:
            print(f"\n{RED}Error Output:\n{stderr}{NC}")
        return False

def get_package_name():
    """
    Dynamically extract package name (applicationId) from Android build files.
    Checks both build.gradle.kts and build.gradle files.
    Returns the package name or None if not found.
    """
    # Check for build.gradle.kts first (newer format)
    gradle_kts_path = Path("android/app/build.gradle.kts")
    gradle_path = Path("android/app/build.gradle")

    # Try build.gradle.kts first
    if gradle_kts_path.exists():
        try:
            with open(gradle_kts_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Pattern for Kotlin DSL: applicationId = "com.example.app"
                match = re.search(r'applicationId\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    package_name = match.group(1)
                    return package_name
        except Exception as e:
            print(f"{YELLOW}Warning: Could not read {gradle_kts_path}: {e}{NC}")

    # Try build.gradle (Groovy format)
    if gradle_path.exists():
        try:
            with open(gradle_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Pattern for Groovy: applicationId "com.example.app"
                match = re.search(r'applicationId\s+["\']([^"\']+)["\']', content)
                if match:
                    package_name = match.group(1)
                    return package_name
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
    manifest_path = Path("android/app/src/main/AndroidManifest.xml")

    if not manifest_path.exists():
        print(f"{YELLOW}Warning: AndroidManifest.xml not found at {manifest_path}{NC}")
        return None

    try:
        with open(manifest_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Pattern to match android:label="App Name" or android:label="@string/app_name"
            match = re.search(r'android:label="([^"]+)"', content)
            if match:
                label = match.group(1)
                # If it's a string resource reference, try to get actual value
                if label.startswith('@string/'):
                    # For now, return a fallback. Could be enhanced to read strings.xml
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
    # and other special characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Remove any remaining special characters except alphanumeric, spaces, hyphens, underscores
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace multiple spaces/hyphens with single underscore
    name = re.sub(r'[-\s]+', '_', name)
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
        arch_match = re.search(r'(arm64-v8a|armeabi-v7a|x86|x86_64)', file_path.name)

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

def display_apk_size():
    """Function to display APK size"""
    apk_dir = Path("build/app/outputs/flutter-apk")
    apk_files = list(apk_dir.glob("*.apk")) if apk_dir.exists() else []
    if apk_files:
        for apk_path in apk_files:
            size_bytes = apk_path.stat().st_size
            size_mb = round(size_bytes / 1048576, 2)
            print(f"{BLUE}APK: {apk_path.name} | Size: {size_mb} MB{NC}")
    else:
        print(f"{RED}APK file not found in {apk_dir}{NC}")

def display_aab_size():
    """Function to display AAB size"""
    aab_dir = Path("build/app/outputs/bundle/release")
    aab_files = list(aab_dir.glob("*.aab")) if aab_dir.exists() else []
    if aab_files:
        for aab_path in aab_files:
            size_bytes = aab_path.stat().st_size
            size_mb = round(size_bytes / 1048576, 2)
            print(f"{BLUE}AAB: {aab_path.name} | Size: {size_mb} MB{NC}")
    else:
        print(f"{RED}AAB file not found in {aab_dir}{NC}")

def run_flutter_command(cmd_list, description):
    """
    Runs a flutter/dart command with a loading spinner.
    Parameters:
        cmd_list: List of command arguments
        description: Description to show with spinner
    """
    # Windows compatibility for shell commands - NEW LINE ADDED HERE
    shell_needed = (is_windows() and cmd_list[0] in ['timeout', 'start', 'flutter', 'dart']) or cmd_list[0] == 'pod'

    process = subprocess.Popen(
        cmd_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell_needed,  # NEW PARAMETER ADDED HERE
        encoding='utf-8',  # Fix Windows encoding issue
        errors='replace'  # Replace problematic characters instead of crashing
    )
    return show_loading(description, process)

@timer_decorator
def build_apk():
    """Build APK (Full Process)"""
    print(f"{YELLOW}Building APK (Full Process)...{NC}\n")

    # Clean the project
    run_flutter_command(["flutter", "clean"], "Cleaning project...                                   ")

    # Get dependencies
    run_flutter_command(["flutter", "pub", "get"], "Getting dependencies...                              ")

    # Generate localizations
    run_flutter_command(["flutter", "gen-l10n"], "Generating localizations...                          ")

    # Generate build files
    run_flutter_command(["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"], "Generating build files...                            ")

    # Build the APK
    run_flutter_command([
        "flutter", "build", "apk", "--release", "--obfuscate", "--target-platform", "android-arm64", "--split-debug-info=./"
    ], "Building APK...                                      ")
    print(f"\n{GREEN}✓ APK built successfully!{NC}")

    # Rename APK files with app label and date
    apk_dir = Path("build/app/outputs/flutter-apk")
    rename_build_files(apk_dir, "apk")

    # Display APK size
    display_apk_size()

    # Open the directory containing the APK
    open_directory("build/app/outputs/flutter-apk/")

@timer_decorator
def build_apk_split_per_abi():
    """Build APK with --split-per-abi"""
    print(f"{YELLOW}Building APK (split-per-abi)...{NC}\n")
    # Clean the project
    run_flutter_command(["flutter", "clean"], "Cleaning project...                                   ")
    # Get dependencies
    run_flutter_command(["flutter", "pub", "get"], "Getting dependencies...                              ")
    # Generate localizations
    run_flutter_command(["flutter", "gen-l10n"], "Generating localizations...                          ")
    # Generate build files
    run_flutter_command(["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"], "Generating build files...                            ")
    # Build APK with split-per-abi
    run_flutter_command([
        "flutter", "build", "apk", "--release", "--split-per-abi", "--obfuscate", "--split-debug-info=./"
    ], "Building APK (split-per-abi)...                      ")
    print(f"\n{GREEN}✓ APK (split-per-abi) built successfully!{NC}")

    # Rename APK files with app label and date
    apk_dir = Path("build/app/outputs/flutter-apk")
    rename_build_files(apk_dir, "apk")

    # Display APK size
    display_apk_size()
    # Open the directory containing the APK
    open_directory("build/app/outputs/flutter-apk/")

@timer_decorator
def build_aab():
    """Build AAB"""
    print(f"{YELLOW}Building AAB...{NC}\n")
    # Clean the project
    run_flutter_command(["flutter", "clean"], "Cleaning project...                                   ")
    # Get dependencies
    run_flutter_command(["flutter", "pub", "get"], "Getting dependencies...                              ")
    # Generate localizations
    run_flutter_command(["flutter", "gen-l10n"], "Generating localizations...                          ")
    # Generate build files
    run_flutter_command(["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"], "Generating build files...                            ")
    # Build AAB
    run_flutter_command(["flutter", "build", "appbundle", "--release", "--obfuscate", "--split-debug-info=./"], "Building AAB...                                      ")
    print(f"\n{GREEN}✓ AAB built successfully!{NC}")

    # Rename AAB files with app label and date
    aab_dir = Path("build/app/outputs/bundle/release")
    rename_build_files(aab_dir, "aab")

    # Display AAB size
    display_aab_size()
    # Open the directory containing the AAB
    open_directory("build/app/outputs/bundle/release/")

def generate_lang():
    """Generate localization files"""
    # Run flutter gen-l10n to generate localization files
    run_flutter_command(["flutter", "gen-l10n"], "Generating localizations                              ")
    print(f"\n{CHECKMARK}  Localizations generated successfully.")

def run_build_runner():
    """Run build_runner to generate Dart code"""
    print(f"{YELLOW}Executing build_runner...{NC}  \n")
    run_flutter_command(["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"], "Running build_runner     ")

@timer_decorator
def full_setup():
    """Perform full project setup"""
    print(f"{YELLOW}Performing full setup...{NC}  \n")
    # Clean the project
    run_flutter_command(["flutter", "clean"], "Cleaning project...                                  ")
    # Upgrade dependencies
    run_flutter_command(["flutter", "pub", "upgrade"], "Upgrading dependencies...                            ")
    # Run build_runner
    run_flutter_command(["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"], "Running build_runner...                              ")
    # Generate localizations
    run_flutter_command(["flutter", "gen-l10n"], "Generating localizations...                          ")
    # Refresh dependencies
    run_flutter_command(["flutter", "pub", "upgrade"], "Refreshing dependencies...                           ")
    # Analyze code
    run_flutter_command(["flutter", "analyze"], "Analyzing code...                                    ")
    # Format code
    run_flutter_command(["dart", "format", "."], "Formatting code...                                   ")
    print(f"\n {GREEN}✓  Full setup completed successfully.  {NC}")

def repair_cache():
    """Repair pub cache"""
    print(f"{YELLOW}Repairing pub cache...{NC}\n")
    run_flutter_command(["flutter", "pub", "cache", "repair"], "Repairing pub cache...                               ")
    print(f"\n {GREEN}✓  Pub cache repaired successfully.  {NC}")

@timer_decorator
def cleanup_project():
    """Clean up project"""
    print(f"{YELLOW}Cleaning up project...{NC}\n")
    run_flutter_command(["flutter", "clean"], "Cleaning project...                                   ")
    # Get dependencies
    run_flutter_command(["flutter", "pub", "get"], "Getting dependencies...                              ")

    #fix code Issues
    run_flutter_command(["dart", "fix", "--apply"], "Fixing code issues...                                   ")

    # Format code
    run_flutter_command(["dart", "format", "."], "Following dart guidelines...                                   ")

    #Upgrade with major version
    run_flutter_command(["flutter", "pub", "upgrade", "--major-versions"], "Upgrading major versions...                            ")
    print(f"\n{GREEN}✓ Project cleaned successfully!{NC}")

@timer_decorator
def release_run():
    """Build & Install Release APK"""
    print(f"{YELLOW}Building & Installing Release APK...{NC}\n")
    run_flutter_command(["flutter", "clean"], "Cleaning project...                                   ")
    run_flutter_command(["flutter", "pub", "get"], "Getting dependencies...                              ")
    run_flutter_command(["flutter", "gen-l10n"], "Generating localizations...                          ")
    run_flutter_command(["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"], "Generating build files...                            ")
    run_flutter_command(["flutter", "build", "apk", "--release", "--obfuscate", "--target-platform", "android-arm64", "--split-debug-info=./"], "Building APK...                                      ")

    # Rename APK files with app label and date
    apk_dir = Path("build/app/outputs/flutter-apk")
    rename_build_files(apk_dir, "apk")

    display_apk_size()
    install_result = install_apk()
    if install_result:
        print(f"\n{GREEN}✓ APK built and installed successfully!{NC}")
    else:
        print(f"\n{RED}✗ APK built but install failed!{NC}")

def install_apk():
    """
    Installs the built APK on a connected Android device using adb.
    Tries to install arm64-v8a APK first if available.
    Handles signature mismatch by uninstalling existing app first.
    Automatically launches the app after successful installation.
    """
    apk_dir = Path("build/app/outputs/flutter-apk")
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
    success = run_flutter_command(["adb", "install", "-r", target_apk], "Installing on device...                              ")

    if not success:
        # Get package name dynamically
        package_name = get_package_name()
        if not package_name:
            print(f"{RED}Cannot proceed without package name{NC}")
            return False

        print(f"{YELLOW}Installation failed, trying to uninstall existing app first...{NC}")
        print(f"{BLUE}Package name: {package_name}{NC}")

        # Try to uninstall existing app first using dynamic package name
        run_flutter_command(["adb", "uninstall", package_name], "Uninstalling existing app...                        ")
        # Then try to install again
        success = run_flutter_command(["adb", "install", target_apk], "Reinstalling on device...                           ")

    # Launch app after successful installation
    if success:
        package_name = get_package_name()
        if package_name:
            print(f"{YELLOW}Launching app...{NC}")
            # Launch the app using monkey command (works on all devices)
            launch_success = run_flutter_command(
                ["adb", "shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"],
                "Starting app on device...                           "
            )
            if launch_success:
                print(f"{GREEN}✓ App launched successfully!{NC}")
            else:
                print(f"{YELLOW}App installed but failed to launch. Please open manually.{NC}")
        else:
            print(f"{YELLOW}App installed but package name not found for launching.{NC}")

    return success

@timer_decorator
def update_pods():
    """Update iOS pods"""
    if is_windows():
        print(f"{YELLOW}iOS pods are not supported on Windows{NC}")
        print(f"{BLUE}This command is only available on macOS and Linux{NC}")
        return
    
    print(f"{YELLOW}Updating iOS pods...{NC}\n")
    # Navigate to iOS directory
    current_dir = os.getcwd()
    os.chdir("ios")
    # Delete Podfile.lock
    try:
        os.remove("Podfile.lock")
        # Use a dummy process for the loading animation
        if is_windows():
            run_flutter_command(["timeout", "/t", "1", "/nobreak", ">nul"], "Removing Podfile.lock                                 ")
        else:
            run_flutter_command(["sleep", "0.1"], "Removing Podfile.lock                                 ")
    except FileNotFoundError:
        pass
    # Update pod repo
    run_flutter_command(["pod", "repo", "update"], "Updating pod repository                               ")
    # Install pods
    run_flutter_command(["pod", "install"], "Installing pods                                       ")
    # Return to root directory
    os.chdir(current_dir)
    print(f"\n{GREEN}✓ iOS pods updated successfully!{NC}")

# ============================================================================
# GIT TAG FUNCTIONS
# ============================================================================

def get_version_from_pubspec():
    """Get the version from pubspec.yaml using regex"""
    if os.path.isfile("pubspec.yaml"):
        with open("pubspec.yaml", 'r', encoding='utf-8') as file:
            try:
                content = file.read()
                # Use regex to find the version field in pubspec.yaml
                version_match = re.search(r'^version:\s*(.+)$', content, re.MULTILINE)
                if version_match:
                    version = version_match.group(1).strip()
                    # Remove quotes if present and split by + to get only version number
                    version = version.strip('"\'').split('+')[0]
                    return version
                else:
                    print(f"{RED}Error: Could not find 'version' field in pubspec.yaml.{NC}")
                    return None
            except Exception as e:
                print(f"{RED}Error: Could not read pubspec.yaml: {e}{NC}")
                return None
    else:
        print(f"{RED}Error: pubspec.yaml not found in the current directory.{NC}")
        print(f"Please run this command from the root of a Flutter project.")
        return None

def parse_version(version_str):
    """Parse version string (e.g., 'v1.2.3' or '1.2.3') into tuple (1, 2, 3)"""
    # Remove 'v' prefix if present
    version_str = version_str.lstrip('v')
    try:
        parts = version_str.split('.')
        return tuple(int(p) for p in parts[:3])  # Return only major.minor.patch
    except:
        return None

def get_all_tags():
    """Get all tags from both local and remote repositories"""
    all_tags = set()
    
    # Get local tags
    try:
        result = subprocess.run(["git", "tag", "-l"],
                              capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.stdout.strip():
            local_tags = result.stdout.strip().split('\n')
            all_tags.update(local_tags)
    except Exception as e:
        print(f"{YELLOW}Warning: Could not get local tags: {e}{NC}")
    
    # Get remote tags
    try:
        result = subprocess.run(["git", "ls-remote", "--tags", "origin"],
                              capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                # Extract tag name from "hash refs/tags/v1.0.0"
                if 'refs/tags/' in line:
                    tag = line.split('refs/tags/')[-1]
                    # Skip ^{} references
                    if not tag.endswith('^{}'):
                        all_tags.add(tag)
    except Exception as e:
        print(f"{YELLOW}Warning: Could not get remote tags: {e}{NC}")
    
    return sorted(all_tags)

def increment_version(version_tuple):
    """Increment patch version: (1, 2, 3) -> (1, 2, 4)"""
    major, minor, patch = version_tuple
    return (major, minor, patch + 1)

def get_build_number_from_pubspec():
    """Get the build number from pubspec.yaml (e.g., from '1.0.0+5' returns 5)"""
    if os.path.isfile("pubspec.yaml"):
        with open("pubspec.yaml", 'r', encoding='utf-8') as file:
            try:
                content = file.read()
                # Find version line with build number
                version_match = re.search(r'^version:\s*["\']?([\d\.]+)\+(\d+)["\']?', content, re.MULTILINE)
                if version_match:
                    build_number = int(version_match.group(2))
                    return build_number
                return None
            except Exception:
                return None
    return None

def update_pubspec_version(new_version):
    """Update version in pubspec.yaml file, preserving and incrementing build number
    Returns: (success, build_number) tuple
    """
    if not os.path.isfile("pubspec.yaml"):
        print(f"{RED}Error: pubspec.yaml not found in the current directory.{NC}")
        return (False, None)

    try:
        with open("pubspec.yaml", 'r', encoding='utf-8') as file:
            content = file.read()

        # Get current build number
        current_build = get_build_number_from_pubspec()

        # Increment build number or start from 1
        new_build = (current_build + 1) if current_build is not None else 1

        # Create new version string with build number
        new_version_with_build = f"{new_version}+{new_build}"

        # Find the version line and replace it
        # Match version with or without build number (e.g., "1.0.0" or "1.0.0+1")
        new_content = re.sub(
            r'^version:\s*["\']?[\d\.]+(\+\d+)?["\']?',
            f'version: {new_version_with_build}',
            content,
            flags=re.MULTILINE
        )

        # Write back to file
        with open("pubspec.yaml", 'w', encoding='utf-8') as file:
            file.write(new_content)

        print(f"{GREEN}  Build number: {current_build or 0} → {new_build}{NC}")
        return (True, new_build)
    except Exception as e:
        print(f"{RED}Error updating pubspec.yaml: {e}{NC}")
        return (False, None)

def commit_version_change(version, build_number=None):
    """Commit the pubspec.yaml version change"""
    # Add pubspec.yaml to staging
    result = subprocess.run(
        ["git", "add", "pubspec.yaml"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    if result.returncode != 0:
        print(f"{RED}Failed to stage pubspec.yaml{NC}")
        return False

    # Commit with version bump message
    if build_number:
        commit_message = f"chore: bump version to {version}+{build_number}"
    else:
        commit_message = f"chore: bump version to {version}"

    result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    if result.returncode != 0:
        print(f"{RED}Failed to commit version change{NC}")
        return False

    return True

def create_and_push_tag():
    """Create git tag by auto-incrementing the latest existing tag and push to remote"""
    print(f"{YELLOW}Creating and pushing git tag...{NC}\n")

    # Get all existing tags
    print(f"{BLUE}Checking existing tags...{NC}")
    all_tags = get_all_tags()

    if all_tags:
        print(f"{GREEN}Found {len(all_tags)} existing tag(s):{NC}")
        for tag in all_tags[-5:]:  # Show last 5 tags
            print(f"  • {tag}")
        if len(all_tags) > 5:
            print(f"  ... and {len(all_tags) - 5} more")
        print()

    # Find the latest version
    latest_version = None
    latest_tag = None

    for tag in all_tags:
        parsed = parse_version(tag)
        if parsed:
            if latest_version is None or parsed > latest_version:
                latest_version = parsed
                latest_tag = tag

    # Determine new version
    if latest_version:
        new_version = increment_version(latest_version)
        new_tag = f"v{new_version[0]}.{new_version[1]}.{new_version[2]}"
        new_version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
        print(f"{BLUE}Latest tag: {latest_tag} → New tag: {new_tag}{NC}\n")
    else:
        # No existing tags, use version from pubspec
        version = get_version_from_pubspec()
        if not version:
            print(f"{YELLOW}No existing tags found and cannot read pubspec version.{NC}")
            print(f"{YELLOW}Using default: v1.0.0{NC}\n")
            new_tag = "v1.0.0"
            new_version_str = "1.0.0"
        else:
            new_tag = f"v{version}"
            new_version_str = version
            print(f"{BLUE}No existing tags found. Creating first tag: {new_tag}{NC}\n")

    # Confirm with user
    user_input = input(f"Update pubspec.yaml, commit and create tag {GREEN}{new_tag}{NC}? (Y/n): ")
    if user_input.lower() == 'n':
        print(f"{YELLOW}Operation cancelled.{NC}")
        return False

    # Step 1: Update pubspec.yaml version
    print(f"{BLUE}Updating pubspec.yaml version to {new_version_str}...{NC}")
    success, build_number = update_pubspec_version(new_version_str)
    if not success:
        print(f"{RED}Failed to update pubspec.yaml{NC}")
        return False
    print(f"{GREEN}✓ pubspec.yaml updated to {new_version_str}+{build_number}{NC}")

    # Step 2: Commit the version change
    print(f"{BLUE}Committing version change...{NC}")
    if not commit_version_change(new_version_str, build_number):
        print(f"{RED}Failed to commit version change{NC}")
        return False
    print(f"{GREEN}✓ Version change committed{NC}")

    # Step 3: Create git tag
    success = run_flutter_command(["git", "tag", new_tag], f"Creating tag {new_tag}...                             ")
    if not success:
        print(f"{RED}Failed to create git tag.{NC}")
        return False

    # Step 4: Push commit to remote
    print(f"{BLUE}Pushing commit to remote...{NC}")
    success = run_flutter_command(["git", "push"], f"Pushing commit...                                   ")
    if not success:
        print(f"{RED}Failed to push commit to remote.{NC}")
        return False

    # Step 5: Push tag to remote
    success = run_flutter_command(["git", "push", "-u", "origin", new_tag], f"Pushing tag to remote...                            ")
    if not success:
        print(f"{RED}Failed to push tag to remote.{NC}")
        return False

    print(f"\n{GREEN}✓ Version {new_version_str}+{build_number} updated, committed, and git tag {new_tag} created and pushed successfully!{NC}")
    return True

def uninstall_app():
    """Uninstall the app from connected device (Android/iOS)"""
    print(f"{YELLOW}Uninstalling app from device...{NC}\n")

    # Check which device is connected
    try:
        # Check for iOS simulator
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

    try:
        # Check for Android device
        android_check = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        android_connected = android_check.returncode == 0 and len(android_check.stdout.strip().split('\n')) > 1
    except (FileNotFoundError, subprocess.TimeoutExpired):
        android_connected = False

    # Handle iOS Simulator
    if ios_connected and not android_connected:
        print(f"{BLUE}iOS Simulator detected{NC}")

        # Get bundle identifier from iOS
        info_plist_path = Path("ios/Runner/Info.plist")
        if not info_plist_path.exists():
            print(f"{RED}Error: Info.plist not found{NC}")
            return False

        try:
            # Extract bundle identifier using PlistBuddy
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
                # Fallback to package name from Android
                bundle_id = get_package_name()
                if not bundle_id:
                    print(f"{RED}Cannot get bundle identifier{NC}")
                    return False

            print(f"{BLUE}Bundle ID: {bundle_id}{NC}")

            # Uninstall from iOS simulator
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

        # Get package name dynamically
        package_name = get_package_name()
        if not package_name:
            print(f"{RED}Cannot proceed without package name{NC}")
            return False

        print(f"{BLUE}Package name: {package_name}{NC}")
        success = run_flutter_command(
            ["adb", "uninstall", package_name],
            "Uninstalling from Android...                        "
        )

        if success:
            print(f"\n{GREEN}✓ App uninstalled successfully from Android!{NC}")
        else:
            print(f"\n{RED}✗ Failed to uninstall app from Android!{NC}")
        return success

    else:
        print(f"{RED}No device/simulator detected!{NC}")
        print(f"{YELLOW}Please connect an Android device or start an iOS simulator{NC}")
        return False

@timer_decorator
def smart_commit():
    """Generate git diff, create commit message using Gemini AI, and commit"""
    print(f"{YELLOW}Smart Git Commit...{NC}\n")

    current_dir = os.getcwd()

    # Check if git repository
    try:
        subprocess.run(["git", "status"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print(f"{RED}Error: Not a git repository or git not available{NC}")
        return False

    # Check for changes
    try:
        result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True, encoding='utf-8', errors='replace')
        staged_changes = result.stdout.strip()

        result = subprocess.run(["git", "diff"], capture_output=True, text=True, encoding='utf-8', errors='replace')
        unstaged_changes = result.stdout.strip()

        if not staged_changes and not unstaged_changes:
            print(f"{YELLOW}No changes detected to commit{NC}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"{RED}Error checking git changes: {e}{NC}")
        return False

    # Get all changes (staged + unstaged)
    try:
        result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True, encoding='utf-8', errors='replace')
        all_changes = result.stdout.strip()

        if not all_changes:
            # If no changes from HEAD, get staged changes only
            all_changes = staged_changes

    except subprocess.CalledProcessError:
        all_changes = staged_changes + "\n" + unstaged_changes

    if not all_changes:
        print(f"{YELLOW}No changes to analyze{NC}")
        return False

    # Import Gemini API
    try:
        script_dir = Path(__file__).parent
        gemini_script = Path.home() / "scripts" / "flutter-tools" / "gemini_api.py"

        if not gemini_script.exists():
            print(f"{RED}Error: gemini_api.py not found{NC}")
            return False

        # Import the function
        sys.path.insert(0, str(Path.home() / "scripts" / "flutter-tools"))
        from gemini_api import generate_commit_message

    except ImportError as e:
        print(f"{RED}Error importing Gemini API: {e}{NC}")
        return False

    # Generate commit message
    commit_message = generate_commit_message(all_changes)

    if not commit_message:
        print(f"{RED}Failed to generate commit message{NC}")
        return False

    print(f"\n{BLUE}Generated commit message:{NC}")
    
    # Process commit message to add "-" to description lines
    lines = commit_message.split('\n')
    processed_lines = []
    
    for i, line in enumerate(lines):
        # Skip the first line (title) and empty lines
        if i == 0 or line.strip() == "":
            processed_lines.append(line)
        else:
            # Add "-" to non-empty description lines
            if line.strip():
                processed_lines.append(f"- {line}")
            else:
                processed_lines.append(line)
    
    formatted_commit_message = '\n'.join(processed_lines)
    print(f"{GREEN}{formatted_commit_message}{NC}\n")

    # Ask for confirmation
    user_input = input(f"Proceed with this commit? (y/N): ")
    if user_input.lower() != 'y':
        print(f"{YELLOW}Commit cancelled{NC}")
        return False

    # Stage all changes if there are unstaged changes
    if unstaged_changes:
        print(f"{YELLOW}Staging all changes...{NC}")
        try:
            subprocess.run(["git", "add", "."], check=True)
            print(f"{GREEN}✓ Changes staged{NC}")
        except subprocess.CalledProcessError as e:
            print(f"{RED}Error staging changes: {e}{NC}")
            return False

    # Commit with generated message
    try:
        subprocess.run(["git", "commit", "-m", formatted_commit_message], check=True)
        print(f"\n{GREEN}✓ Commit successful!{NC}")
        
        # Wait 1.5 seconds to show success message
        time.sleep(1.5)

        # Clear terminal after successful commit
        if is_windows():
            os.system('cls')
        else:
            os.system('clear')
        
        print(f"{GREEN}✓ Commit completed and terminal cleared!{NC}")
        print(f"{BLUE}Ready for next commit 🚀{NC}\n")
        
        return True

    except subprocess.CalledProcessError as e:
        print(f"{RED}Error creating commit: {e}{NC}")
        return False

def create_page(page_name):
    """Create page structure"""
    print(f"{YELLOW}Creating page...{NC}\n")
    if not page_name:
        print(f"{RED}Error: Page name is required.{NC}")
        print(f"Usage: {sys.argv[0]} page <page_name>")
        sys.exit(1)
    # Run the create_page with the page name using global path
    try:
        create_page_script = str(Path.home() / "scripts" / "flutter-tools" / "create_page.py")
        subprocess.run([sys.executable, create_page_script, "page", page_name], check=True)
    except subprocess.CalledProcessError:
        print(f"{RED}Error: Failed to run page generator.{NC}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"{RED}Error: create_page.py not found.{NC}")
        print("Make sure create_page.py exists at ~/scripts/flutter-tools/")
        sys.exit(1)

def show_usage():
    """Show usage information"""
    print(f"{YELLOW}Usage: {sys.argv[0]} [command]{NC}")
    print("\nAvailable commands:")
    print("  apk          Build release APK (Full Process)")
    print("  apk-split    Build APK with --split-per-abi")
    print("  aab          Build release AAB")
    print("  lang         Generate localization files")
    print("  db           Run build_runner")
    print("  setup        Perform full project setup")
    print("  cache-repair Repair pub cache")
    print("  cleanup      Clean project and get dependencies")
    print("  release-run  Build & install release APK on connected device")
    print("  install      Install built APK on connected device")
    print("  uninstall    Uninstall app from connected device")
    print("  pod          Update iOS pods")
    print("  tag          Create and push git tag from pubspec version")
    print("  commit       Smart git commit with AI-generated message")
    print("  page         Create page structure (usage: {sys.argv[0]} page <page_name>)")
    sys.exit(1)

def main():
    """Main function"""
    # Create required directories if they don't exist
    os.makedirs("build/app/outputs/flutter-apk", exist_ok=True)
    os.makedirs("build/app/outputs/bundle/release", exist_ok=True)
    if len(sys.argv) < 2:
        show_usage()
    command = sys.argv[1].lower()
    if command == "apk":
        build_apk()
    elif command == "apk-split":
        build_apk_split_per_abi()
    elif command == "aab":
        build_aab()
    elif command == "lang":
        generate_lang()
    elif command == "db":
        run_build_runner()
    elif command == "setup":
        full_setup()
    elif command == "cache-repair":
        repair_cache()
    elif command == "cleanup":
        cleanup_project()
    elif command == "release-run":
        release_run()
    elif command == "install":
        install_apk()
    elif command == "uninstall":
        uninstall_app()
    elif command == "pod":
        update_pods()
    elif command == "tag":
        create_and_push_tag()
    elif command == "commit":
        smart_commit()
    elif command == "page":
        if len(sys.argv) < 3:
            print(f"{RED}Error: Page name is required.{NC}")
            print(f"Usage: {sys.argv[0]} page <page_name>")
            sys.exit(1)
        create_page(sys.argv[2])
    else:
        show_usage()

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nProcess interrupted. Exiting...")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    main()
