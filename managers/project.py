#!/usr/bin/env python3
"""
Project Manager - Setup, cleanup, build_runner, pods functions
"""

import os
import sys
import subprocess
from pathlib import Path

from common_utils import (
    RED, GREEN, YELLOW, NC, CHECKMARK,
    timer_decorator,
    is_windows,
)
from managers.build import run_flutter_command


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

    # fix code Issues
    run_flutter_command(["dart", "fix", "--apply"], "Fixing code issues...                                   ")

    # Format code
    run_flutter_command(["dart", "format", "."], "Following dart guidelines...                                   ")

    # Upgrade with major version
    run_flutter_command(["flutter", "pub", "upgrade", "--major-versions"], "Upgrading major versions...                            ")
    print(f"\n{GREEN}✓ Project cleaned successfully!{NC}")


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
