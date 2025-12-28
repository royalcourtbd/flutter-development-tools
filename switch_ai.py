#!/usr/bin/env python3
"""
AI Service Switcher
Usage: python3 switch_ai.py [groq|mistral|sambanova|openrouter]
"""

import sys
import os
import subprocess
from pathlib import Path

# Import common utilities
from common_utils import (
    RED, GREEN, YELLOW, BLUE, NC, CHECKMARK, CROSS,
    timer_decorator,
    run_command_with_spinner,
    read_env_value,
    update_env_value,
    get_user_shell,
    is_windows
)

ENV_FILE = ".env"

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

def reload_shell_config():
    """
    Reload shell configuration after successful switch
    Supports zsh, bash, fish on Unix systems
    """
    if is_windows():
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
