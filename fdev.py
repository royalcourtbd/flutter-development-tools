#!/usr/bin/env python3
import os
import sys
import time
import signal
import platform
import subprocess
import glob
import re  # Added for git tag functionality
from functools import wraps
from pathlib import Path
import json

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'
MAGENTA = '\033[0;35m'  
CHECKMARK = '\033[32m✓\033[0m' 
CROSS = '\033[31m𐄂\033[0m'

def timer_decorator(func):
    """
    Decorator to automatically add timer functionality to any function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Execute the original function
        result = func(*args, **kwargs)
        
        end_time = time.time()
        total_seconds = end_time - start_time
        minutes, seconds = divmod(total_seconds, 60)
        
        print(f"\n{BLUE}======================================================{NC}")
        print(f"{BLUE}Total time taken: {int(minutes)} minute(s) and {seconds:.2f} seconds.{NC}")
        print(f"{BLUE}======================================================{NC}")
        
        return result
    return wrapper

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
        #     print(f"\n{GREEN}Output:\n{stdout.decode()}{NC}")
        return True
    else:
        print(f"\b{CROSS} ", flush=True)
        # Nicher ei stdout statement ta comment out korle r command er out put dekha jabe na.
        if stdout:
            print(f"\n{GREEN}Output:\n{stdout.decode()}{NC}")
        if stderr:
            print(f"\n{RED}Error Output:\n{stderr.decode()}{NC}")
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

def run_flutter_command(cmd_list, description):
    """
    Runs a flutter/dart command with a loading spinner.
    Parameters:
        cmd_list: List of command arguments
        description: Description to show with spinner
    """
    # Windows compatibility for shell commands - NEW LINE ADDED HERE
    shell_needed = (platform.system() == "Windows" and cmd_list[0] in ['timeout', 'start', 'flutter', 'dart']) or cmd_list[0] == 'pod'
    
    process = subprocess.Popen(
        cmd_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell_needed  # NEW PARAMETER ADDED HERE
    )
    return show_loading(description, process)

def open_directory(directory_path):
    """Opens a directory based on the operating system"""
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", directory_path])
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", directory_path])
        elif platform.system() == "Windows":
            # Convert to absolute path and use Windows path separators
            abs_path = os.path.abspath(directory_path)
            # Use explorer to open the directory
            subprocess.run(["explorer", abs_path], shell=True)
        else:
            print(f"Cannot open directory automatically. Please check: {directory_path}")
    except Exception as e:
        print(f"Error opening directory: {e}")
        print(f"Please check: {directory_path}")

@timer_decorator
def build_apk():
    """Build APK (Full Process)"""
    print(f"{YELLOW}Building APK (Full Process)...{NC}\n")

    # Clean the project
    run_flutter_command(["flutter", "clean"], "Cleaning project...                                   ")
    
    # Get dependencies
    run_flutter_command(["flutter", "pub", "get"], "Getting dependencies...                              ")
    
    # Generate build files
    run_flutter_command(["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"], "Generating build files...                            ")
    
    # Build the APK
    run_flutter_command([
        "flutter", "build", "apk", "--release", "--obfuscate", "--target-platform", "android-arm64", "--split-debug-info=./"
    ], "Building APK...                                      ")
    print(f"\n{GREEN}✓ APK built successfully!{NC}")
    
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
    # Generate build files
    run_flutter_command(["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"], "Generating build files...                            ")
    # Build APK with split-per-abi
    run_flutter_command([
        "flutter", "build", "apk", "--release", "--split-per-abi", "--obfuscate", "--split-debug-info=./"
    ], "Building APK (split-per-abi)...                      ")
    print(f"\n{GREEN}✓ APK (split-per-abi) built successfully!{NC}")
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
    # Generate build files
    run_flutter_command(["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"], "Generating build files...                            ")
    # Build AAB
    run_flutter_command(["flutter", "build", "appbundle", "--release", "--obfuscate", "--split-debug-info=./"], "Building AAB...                                      ")
    print(f"\n{GREEN}✓ AAB built successfully!{NC}")
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
    if platform.system() == "Windows":
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
        if platform.system() == "Windows":
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

def create_and_push_tag():
    """Create git tag from pubspec version and push to remote"""
    print(f"{YELLOW}Creating and pushing git tag...{NC}\n")
    
    # Get version from pubspec.yaml
    version = get_version_from_pubspec()
    if not version:
        return False
    
    tag_name = f"v{version}"
    
    print(f"{BLUE}Version found: {version}{NC}")
    print(f"{BLUE}Tag name: {tag_name}{NC}\n")
    
    # Check if tag already exists
    try:
        result = subprocess.run(["git", "tag", "-l", tag_name], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print(f"{YELLOW}Warning: Tag {tag_name} already exists locally.{NC}")
            user_input = input(f"Do you want to delete and recreate it? (y/N): ")
            if user_input.lower() != 'y':
                print(f"{YELLOW}Operation cancelled.{NC}")
                return False
            # Delete existing tag
            subprocess.run(["git", "tag", "-d", tag_name])
            print(f"{GREEN}Deleted existing local tag: {tag_name}{NC}")
    except Exception as e:
        print(f"{RED}Error checking existing tags: {e}{NC}")
        return False
    
    # Create git tag
    success = run_flutter_command(["git", "tag", tag_name], f"Creating tag {tag_name}...                             ")
    if not success:
        print(f"{RED}Failed to create git tag.{NC}")
        return False
    
    # Push tag to remote
    success = run_flutter_command(["git", "push", "-u", "origin", tag_name], f"Pushing tag to remote...                            ")
    if not success:
        print(f"{RED}Failed to push tag to remote.{NC}")
        return False
    
    print(f"\n{GREEN}✓ Git tag {tag_name} created and pushed successfully!{NC}")
    return True

def uninstall_app():
    """Uninstall the app from connected device"""
    print(f"{YELLOW}Uninstalling app from device...{NC}\n")

    # Get package name dynamically
    package_name = get_package_name()
    if not package_name:
        print(f"{RED}Cannot proceed without package name{NC}")
        return False

    print(f"{BLUE}Package name: {package_name}{NC}")
    success = run_flutter_command(["adb", "uninstall", package_name], "Uninstalling app...                                 ")
    if success:
        print(f"\n{GREEN}✓ App uninstalled successfully!{NC}")
    else:
        print(f"\n{RED}✗ Failed to uninstall app!{NC}")
    return success

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
        result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True)
        staged_changes = result.stdout.strip()

        result = subprocess.run(["git", "diff"], capture_output=True, text=True)
        unstaged_changes = result.stdout.strip()

        if not staged_changes and not unstaged_changes:
            print(f"{YELLOW}No changes detected to commit{NC}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"{RED}Error checking git changes: {e}{NC}")
        return False

    # Get all changes (staged + unstaged)
    try:
        result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True)
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
        if platform.system() == "Windows":
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
