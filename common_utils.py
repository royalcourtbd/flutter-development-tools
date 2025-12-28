#!/usr/bin/env python3
"""
Common Utilities Module
Shared functions and constants for flutter-dev tools
"""

import os
import re
import time
import platform
import subprocess
from functools import wraps
from pathlib import Path

# ============================================================================
# COLOR CONSTANTS
# ============================================================================

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'
MAGENTA = '\033[0;35m'
CHECKMARK = '\033[32m✓\033[0m'
CROSS = '\033[31m✗\033[0m'

# Disable colors on Windows CMD (unless using Windows Terminal)
if platform.system() == "Windows" and not os.environ.get('WT_SESSION'):
    RED = GREEN = YELLOW = BLUE = NC = MAGENTA = ''
    CHECKMARK = '✓'
    CROSS = '✗'

# ============================================================================
# TIMER DECORATOR
# ============================================================================

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

# ============================================================================
# LOADING SPINNER
# ============================================================================

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

# ============================================================================
# COMMAND EXECUTION WITH SPINNER
# ============================================================================

def run_command_with_spinner(cmd_list, description):
    """
    Runs a command with a loading spinner
    Parameters:
        cmd_list: List of command arguments
        description: Description to show with spinner
    Returns:
        True if successful, False otherwise
    """
    shell_needed = platform.system() == "Windows"

    process = subprocess.Popen(
        cmd_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell_needed,
        encoding='utf-8',  # Fix Windows encoding issue
        errors='replace'  # Replace problematic characters instead of crashing
    )
    return show_loading(description, process)

# ============================================================================
# ENVIRONMENT FILE OPERATIONS
# ============================================================================

def read_env_value(key, env_file=".env"):
    """
    Read a value from .env file
    Parameters:
        key: Environment variable key to read
        env_file: Path to .env file (default: ".env")
    Returns:
        Value of the key or None if not found
    """
    if not os.path.exists(env_file):
        return None

    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split('=', 1)[1]
    return None

def update_env_value(key, value, env_file=".env"):
    """
    Update a value in .env file
    Parameters:
        key: Environment variable key to update
        value: New value to set
        env_file: Path to .env file (default: ".env")
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(env_file):
        print(f"{RED}❌ .env file not found!{NC}")
        return False

    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the value using regex
    pattern = f"^{key}=.*$"
    replacement = f"{key}={value}"
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True

# ============================================================================
# PLATFORM DETECTION
# ============================================================================

def is_windows():
    """Check if running on Windows"""
    return platform.system() == "Windows"

def is_macos():
    """Check if running on macOS"""
    return platform.system() == "Darwin"

def is_linux():
    """Check if running on Linux"""
    return platform.system() == "Linux"

def get_user_shell():
    """
    Detect user's shell (zsh, bash, fish, etc.)
    Returns:
        Tuple of (shell_name, config_file_path)
    """
    home = Path.home()
    shell_env = os.environ.get('SHELL', '')

    # Detect shell type
    if 'zsh' in shell_env:
        return ('zsh', home / '.zshrc')
    elif 'bash' in shell_env:
        # Check if .bashrc or .bash_profile exists
        if (home / '.bashrc').exists():
            return ('bash', home / '.bashrc')
        else:
            return ('bash', home / '.bash_profile')
    elif 'fish' in shell_env:
        return ('fish', home / '.config/fish/config.fish')
    else:
        # Default to bash
        return ('bash', home / '.bashrc')

# ============================================================================
# FILE/DIRECTORY OPERATIONS
# ============================================================================

def open_file_with_default_app(file_path):
    """
    Open file with default application based on platform
    Parameters:
        file_path: Path to the file to open
    Returns:
        True if successful, False otherwise
    """
    try:
        if is_macos():
            subprocess.run(['open', file_path])
        elif is_linux():
            subprocess.run(['xdg-open', file_path])
        elif is_windows():
            subprocess.run(['notepad', file_path])
        else:
            print(f"Please manually open: {file_path}")
            return False
        return True
    except Exception as e:
        print(f"Error opening file: {e}")
        print(f"Please manually open: {file_path}")
        return False

def open_directory(directory_path):
    """
    Opens a directory based on the operating system
    Parameters:
        directory_path: Path to the directory to open
    Returns:
        True if successful, False otherwise
    """
    try:
        if is_macos():
            subprocess.run(["open", directory_path])
        elif is_linux():
            subprocess.run(["xdg-open", directory_path])
        elif is_windows():
            # Convert to absolute path and use Windows path separators
            abs_path = os.path.abspath(directory_path)
            # Use explorer to open the directory
            subprocess.run(["explorer", abs_path], shell=True)
        else:
            print(f"Cannot open directory automatically. Please check: {directory_path}")
            return False
        return True
    except Exception as e:
        print(f"Error opening directory: {e}")
        print(f"Please check: {directory_path}")
        return False
