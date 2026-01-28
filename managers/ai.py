#!/usr/bin/env python3
"""
AI Service Manager
Handles AI service switching and status display
"""

import sys
import os
from pathlib import Path

from common_utils import (
    RED, GREEN, YELLOW, BLUE, NC, MAGENTA,
    read_env_value,
    update_env_value,
    is_windows,
)

VALID_SERVICES = ['groq', 'mistral', 'sambanova', 'openrouter']


def get_env_file_path():
    """Get the correct .env file path (installed location)"""
    if is_windows():
        scripts_dir = Path.home() / "scripts" / "flutter-tools"
    else:
        scripts_dir = Path.home() / "scripts" / "flutter-tools"

    env_file = scripts_dir / ".env"

    if env_file.exists():
        return str(env_file)

    # Fallback to current directory
    return ".env"


def show_ai_status():
    """
    Show current AI service and available options with interactive selection
    """
    env_file = get_env_file_path()
    current = read_env_value("DEFAULT_AI_SERVICE", env_file)

    print(f"\n{BLUE}  Current AI:{NC} {GREEN}{current or 'Not configured'}{NC}\n")

    print(f"{YELLOW}  Available services:{NC}")
    for i, service in enumerate(VALID_SERVICES, 1):
        if service == current:
            print(f"    {GREEN}{i}. {service} (active){NC}")
        else:
            print(f"    {BLUE}{i}. {service}{NC}")

    print()

    try:
        choice = input(f"{MAGENTA}  Select [1-{len(VALID_SERVICES)}]: {NC}").strip()

        if not choice:
            return

        index = int(choice) - 1
        if 0 <= index < len(VALID_SERVICES):
            selected = VALID_SERVICES[index]
            if selected == current:
                print(f"\n{YELLOW}  Already using {selected}{NC}")
            else:
                do_switch(current, selected, env_file)
        else:
            print(f"\n{RED}  Invalid choice{NC}")
    except ValueError:
        print(f"\n{RED}  Invalid input{NC}")
    except KeyboardInterrupt:
        print()


def do_switch(current, service, env_file):
    """Perform the actual switch"""
    if update_env_value("DEFAULT_AI_SERVICE", service, env_file):
        print(f"\n{GREEN}  Switched: {BLUE}{current or 'none'}{NC} → {GREEN}{service}{NC}")
    else:
        print(f"\n{RED}  Failed to switch{NC}")


def switch_ai_service(service):
    """
    Switch to specified AI service directly

    Parameters:
        service: Service name to switch to
    """
    service = service.lower()

    if service not in VALID_SERVICES:
        print(f"{RED}Error: Invalid service '{service}'{NC}")
        print(f"{YELLOW}Valid options: {', '.join(VALID_SERVICES)}{NC}")
        sys.exit(1)

    env_file = get_env_file_path()
    current = read_env_value("DEFAULT_AI_SERVICE", env_file)

    if current == service:
        print(f"{YELLOW}Already using: {GREEN}{service}{NC}")
        return

    if update_env_value("DEFAULT_AI_SERVICE", service, env_file):
        print(f"{GREEN}Switched: {BLUE}{current or 'none'}{NC} → {GREEN}{service}{NC}")
    else:
        print(f"{RED}Failed to switch{NC}")
        sys.exit(1)
