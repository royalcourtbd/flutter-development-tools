#!/usr/bin/env python3
"""
AI Service Switcher
Usage: python3 switch_ai.py [groq|mistral|sambanova|openrouter]
"""

import sys
import os
import re
import time
import subprocess
import platform
from pathlib import Path
from functools import wraps

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

ENV_FILE = ".env"

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
        return True
    else:
        print(f"\b{CROSS} ", flush=True)
        if stdout:
            print(f"\n{GREEN}Output:\n{stdout.decode()}{NC}")
        if stderr:
            print(f"\n{RED}Error Output:\n{stderr.decode()}{NC}")
        return False

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
        shell=shell_needed
    )
    return show_loading(description, process)

def read_env_value(key):
    """
    Read a value from .env file
    Parameters:
        key: Environment variable key to read
    Returns:
        Value of the key or None if not found
    """
    if not os.path.exists(ENV_FILE):
        return None

    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split('=', 1)[1]
    return None

def update_env_value(key, value):
    """
    Update a value in .env file
    Parameters:
        key: Environment variable key to update
        value: New value to set
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(ENV_FILE):
        print(f"{RED}❌ .env file not found!{NC}")
        return False

    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the value using regex
    pattern = f"^{key}=.*$"
    replacement = f"{key}={value}"
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True

def show_current_service():
    """
    Show current AI service and usage instructions
    """
    current = read_env_value("DEFAULT_AI_SERVICE")
    if current:
        print(f"{BLUE}📌 Current AI Service: {GREEN}{current}{NC}")
    else:
        print(f"{YELLOW}⚠️  DEFAULT_AI_SERVICE not found in .env{NC}")

    print("")
    print(f"{YELLOW}🔄 To switch service:{NC}")
    print(f"   {BLUE}python3 switch_ai.py groq{NC}")
    print(f"   {BLUE}python3 switch_ai.py mistral{NC}")
    print(f"   {BLUE}python3 switch_ai.py sambanova{NC}")
    print(f"   {BLUE}python3 switch_ai.py openrouter{NC}")

def run_setup():
    """
    Run setup.py after successful AI service switch with loading spinner
    Returns:
        True if successful, False otherwise
    """
    setup_script = Path(__file__).parent / "setup.py"

    if not setup_script.exists():
        print(f"{YELLOW}⚠️  setup.py not found, skipping setup{NC}")
        return False

    print("")
    print(f"{YELLOW}🔧 Running setup.py...{NC}")
    print(f"{BLUE}{'─' * 50}{NC}")

    success = run_command_with_spinner(
        [sys.executable, str(setup_script)],
        f"{YELLOW}Configuring environment...                          {NC}"
    )

    print(f"{BLUE}{'─' * 50}{NC}")

    if success:
        print(f"{GREEN}✅ Setup completed successfully!{NC}")
        return True
    else:
        print(f"{RED}❌ Setup failed!{NC}")
        return False

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

def reload_shell_config():
    """
    Reload shell configuration after successful switch
    Supports zsh, bash, fish on Unix systems
    """
    if platform.system() == "Windows":
        print(f"\n{YELLOW}⚠️  Windows detected - please restart your terminal{NC}")
        return

    print("")
    print(f"{YELLOW}🔄 Reloading shell configuration...{NC}")

    shell_name, config_file = get_user_shell()

    try:
        # Try to source the config file
        subprocess.run(
            [shell_name, "-c", f"source {config_file}"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"{GREEN}✅ Shell configuration reloaded!{NC}")
        print("")
        print(f"{BLUE}💡 If commands are not working, run manually:{NC}")
        print(f"   {GREEN}source {config_file}{NC}")
    except Exception:
        print(f"{YELLOW}⚠️  Please run manually to reload your shell:{NC}")
        print(f"   {GREEN}source {config_file}{NC}")

@timer_decorator
def switch_service(service):
    """
    Switch AI service with full validation and setup
    Parameters:
        service: Service name to switch to
    Returns:
        True if successful, False otherwise
    """
    # Get current service
    current = read_env_value("DEFAULT_AI_SERVICE")

    # Check if trying to switch to the same service
    if current == service:
        print(f"{YELLOW}⚠️  AI Service is already set to: {GREEN}{service}{NC}")
        print(f"   {BLUE}{current} → {service}{NC}")
        print(f"   {YELLOW}No changes made.{NC}")
        return False

    # Update .env file
    print(f"{YELLOW}Switching AI service...{NC}\n")

    if update_env_value("DEFAULT_AI_SERVICE", service):
        print(f"{GREEN}✅ AI Service switched successfully!{NC}")
        print(f"   {BLUE}{current}{NC} → {GREEN}{service}{NC}")

        # Run setup.py after successful switch
        setup_success = run_setup()

        # Reload shell configuration
        reload_shell_config()

        return setup_success
    else:
        print(f"{RED}❌ Failed to update .env file{NC}")
        return False

def main():
    """
    Main function to handle AI service switching
    """
    print(f"{BLUE}{'=' * 50}{NC}")
    print(f"{BLUE}          AI Service Switcher{NC}")
    print(f"{BLUE}{'=' * 50}{NC}\n")

    # Check if .env file exists
    if not os.path.exists(ENV_FILE):
        print(f"{RED}❌ .env file not found!{NC}")
        print(f"{YELLOW}Please create a .env file first{NC}")
        sys.exit(1)

    # If no argument provided, show current service
    if len(sys.argv) < 2:
        show_current_service()
        sys.exit(0)

    service = sys.argv[1].lower()

    # Valid services
    valid_services = ['groq', 'mistral', 'sambanova', 'openrouter']

    if service not in valid_services:
        print(f"{RED}❌ Invalid service: {service}{NC}")
        print(f"{YELLOW}   Valid options: {', '.join(valid_services)}{NC}")
        sys.exit(1)

    # Switch service
    success = switch_service(service)

    if success:
        print(f"\n{GREEN}{'=' * 50}{NC}")
        print(f"{GREEN}🎉 AI Service switch completed successfully!{NC}")
        print(f"{GREEN}{'=' * 50}{NC}")
    else:
        print(f"\n{YELLOW}{'=' * 50}{NC}")
        print(f"{YELLOW}⚠️  Service switch completed with warnings{NC}")
        print(f"{YELLOW}{'=' * 50}{NC}")

if __name__ == "__main__":
    main()
