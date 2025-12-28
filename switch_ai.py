#!/usr/bin/env python3
"""
AI Service Switcher
Usage: python3 switch_ai.py [groq|mistral|sambanova|openrouter]
"""

import sys
import os
import re
import subprocess
from pathlib import Path

ENV_FILE = ".env"

def read_env_value(key):
    """Read a value from .env file"""
    if not os.path.exists(ENV_FILE):
        return None

    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split('=', 1)[1]
    return None

def update_env_value(key, value):
    """Update a value in .env file"""
    if not os.path.exists(ENV_FILE):
        print(f"❌ .env file not found!")
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
    """Show current AI service and usage instructions"""
    current = read_env_value("DEFAULT_AI_SERVICE")
    if current:
        print(f"📌 Current AI Service: {current}")
    else:
        print(f"⚠️  DEFAULT_AI_SERVICE not found in .env")

    print("")
    print("🔄 To switch service:")
    print("   python3 switch_ai.py groq")
    print("   python3 switch_ai.py mistral")
    print("   python3 switch_ai.py sambanova")
    print("   python3 switch_ai.py openrouter")

def run_setup():
    """Run setup.py after successful AI service switch"""
    setup_script = Path(__file__).parent / "setup.py"

    if not setup_script.exists():
        print(f"⚠️  setup.py not found, skipping setup")
        return

    print("")
    print("🔧 Running setup.py...")
    print("─" * 50)

    try:
        result = subprocess.run(
            [sys.executable, str(setup_script)],
            check=True
        )
        print("─" * 50)
        print("✅ Setup completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup failed with error code {e.returncode}")
    except Exception as e:
        print(f"❌ Error running setup: {e}")

def main():
    # Check if .env file exists
    if not os.path.exists(ENV_FILE):
        print(f"❌ .env file not found!")
        sys.exit(1)

    # If no argument provided, show current service
    if len(sys.argv) < 2:
        show_current_service()
        sys.exit(0)

    service = sys.argv[1].lower()

    # Valid services
    valid_services = ['groq', 'mistral', 'sambanova', 'openrouter']

    if service not in valid_services:
        print(f"❌ Invalid service: {service}")
        print(f"   Valid options: {', '.join(valid_services)}")
        sys.exit(1)

    # Get current service
    current = read_env_value("DEFAULT_AI_SERVICE")

    # Check if trying to switch to the same service
    if current == service:
        print(f"⚠️  AI Service is already set to: {service}")
        print(f"   {current} → {service}")
        print(f"   No changes made.")
        sys.exit(0)

    # Update .env file
    if update_env_value("DEFAULT_AI_SERVICE", service):
        print("✅ AI Service switched successfully!")
        print(f"   {current} → {service}")

        # Run setup.py after successful switch
        run_setup()

        # Source zshrc at the end
        print("")
        print("🔄 Reloading shell configuration...")
        try:
            # Note: source command needs to run in the user's shell
            # We can't actually source from Python, but we can remind the user
            subprocess.run(["zsh", "-c", "source ~/.zshrc"], check=False)
            print("✅ Shell configuration reloaded!")
            print("")
            print("💡 If commands are not working, run manually:")
            print("   source ~/.zshrc")
        except Exception:
            print("⚠️  Please run manually to reload your shell:")
            print("   source ~/.zshrc")
    else:
        print("❌ Failed to update .env file")
        sys.exit(1)

if __name__ == "__main__":
    main()
