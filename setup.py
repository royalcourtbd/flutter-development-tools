#!/usr/bin/env python3
"""
Cross-platform setup script for Flutter development tools
Works on macOS, Linux, and Windows
"""

import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Disable colors on Windows CMD (unless using Windows Terminal)
if platform.system() == "Windows" and not os.environ.get('WT_SESSION'):
    RED = GREEN = YELLOW = BLUE = NC = ''

def get_system_info():
    """Get system information"""
    return {
        'platform': platform.system(),
        'home': Path.home(),
        'python': sys.executable
    }

def get_base_python():
    """Get the base Python executable (not venv Python)"""
    # sys.base_executable gives the original Python even when in a venv
    if hasattr(sys, 'base_executable') and sys.base_executable:
        return sys.base_executable
    return sys.executable

def get_dependencies_from_requirements():
    """Read dependencies from requirements.txt file"""
    requirements_file = Path(__file__).parent / 'requirements.txt'
    dependencies = []

    if requirements_file.exists():
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Extract package name (remove version specifiers for import check)
                package_name = line.split('>=')[0].split('==')[0].split('<')[0].strip()
                if package_name:
                    dependencies.append(package_name)

    # Fallback to hardcoded list if requirements.txt not found or empty
    if not dependencies:
        dependencies = ['python-dotenv', 'requests']

    return dependencies


def install_dependencies():
    """Install required Python dependencies to base Python"""
    print(f"{YELLOW}Checking and installing dependencies...{NC}")

    base_python = get_base_python()
    print(f"{BLUE}Using Python: {base_python}{NC}")

    # First try to install from requirements.txt directly
    requirements_file = Path(__file__).parent / 'requirements.txt'
    if requirements_file.exists():
        print(f"{BLUE}Installing from requirements.txt...{NC}")
        install_methods = [
            [base_python, '-m', 'pip', 'install', '-r', str(requirements_file)],
            [base_python, '-m', 'pip', 'install', '--user', '-r', str(requirements_file)],
            [base_python, '-m', 'pip', 'install', '--break-system-packages', '-r', str(requirements_file)],
        ]

        for method in install_methods:
            try:
                subprocess.check_call(method, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"{GREEN}✓ All dependencies installed from requirements.txt{NC}")
                print()
                return
            except subprocess.CalledProcessError:
                continue

        print(f"{YELLOW}Could not install from requirements.txt, trying individual packages...{NC}")

    # Fallback: Install packages individually
    dependencies = get_dependencies_from_requirements()

    for package in dependencies:
        try:
            __import__(package.replace('-', '_'))
            print(f"{GREEN}✓ {package} is already installed{NC}")
        except ImportError:
            print(f"{YELLOW}Installing {package}...{NC}")

            # Try different installation methods using base Python
            install_methods = [
                # Method 1: Standard pip install
                [base_python, '-m', 'pip', 'install', package],
                # Method 2: With --user flag
                [base_python, '-m', 'pip', 'install', '--user', package],
                # Method 3: With --break-system-packages (for externally managed environments)
                [base_python, '-m', 'pip', 'install', '--break-system-packages', package],
            ]

            installed = False
            for method in install_methods:
                try:
                    subprocess.check_call(method,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
                    print(f"{GREEN}✓ Successfully installed {package}{NC}")
                    installed = True
                    break
                except subprocess.CalledProcessError:
                    continue

            if not installed:
                print(f"{RED}✗ Failed to install {package}{NC}")
                print(f"{YELLOW}→ Please install manually:{NC}")
                print(f"{BLUE}   pip3 install --user {package}{NC}")
                print(f"{BLUE}   or{NC}")
                print(f"{BLUE}   pip3 install --break-system-packages {package}{NC}")

    print()

def create_batch_wrapper(script_path, wrapper_path, script_name):
    """Create Windows batch wrapper with base Python path"""
    python_path = get_base_python()
    batch_content = f'''@echo off
"{python_path}" "{script_path}" %*
'''
    with open(wrapper_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    print(f"{GREEN}✓ Created Windows batch wrapper: {wrapper_path}{NC}")

def create_shell_wrapper(script_path, wrapper_path, script_name):
    """Create Unix shell wrapper with base Python path"""
    python_path = get_base_python()
    shell_content = f'''#!/bin/bash
"{python_path}" "{script_path}" "$@"
'''
    with open(wrapper_path, 'w', encoding='utf-8') as f:
        f.write(shell_content)

    # Make executable
    os.chmod(wrapper_path, 0o755)
    print(f"{GREEN}✓ Created shell wrapper: {wrapper_path}{NC}")

def copy_directory(src_dir, dest_dir, dir_name):
    """Copy entire directory with all contents"""
    src_path = src_dir / dir_name
    dest_path = dest_dir / dir_name

    if src_path.exists() and src_path.is_dir():
        # Remove existing directory if exists
        if dest_path.exists():
            shutil.rmtree(dest_path)

        # Copy entire directory
        shutil.copytree(src_path, dest_path)

        # Count files copied
        file_count = sum(1 for _ in dest_path.rglob('*.py'))
        print(f"{GREEN}✓ Copied {dir_name}/ directory ({file_count} Python files){NC}")
        return True
    return False

def setup_windows(system_info):
    """Setup for Windows"""
    print(f"{YELLOW}Setting up for Windows...{NC}")

    home = system_info['home']
    scripts_dir = home / 'scripts' / 'flutter-tools'
    bin_dir = home / 'bin'

    # Create directories
    scripts_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Define all Python scripts to copy
    scripts_to_copy = [
        ('fdev.py', 'fdev'),
        ('create_page.py', 'create-page'),
        ('gemini_api.py', 'gemini-api'),
        ('git_diff_output_editor.py', 'git-diff-editor')
    ]

    # Define utility files that need to be copied (no command wrappers needed)
    utility_files = ['common_utils.py', 'switch_ai.py', 'requirements.txt']

    # Define module directories to copy
    module_directories = ['core', 'managers']

    # Copy scripts to scripts directory (if not already there)
    current_dir = Path(__file__).parent

    if current_dir != scripts_dir:
        # Copy main scripts
        for script_file, _ in scripts_to_copy:
            if (current_dir / script_file).exists():
                shutil.copy2(current_dir / script_file, scripts_dir / script_file)
                print(f"{GREEN}✓ Copied {script_file}{NC}")

        # Copy utility files
        for util_file in utility_files:
            if (current_dir / util_file).exists():
                shutil.copy2(current_dir / util_file, scripts_dir / util_file)
                print(f"{GREEN}✓ Copied {util_file}{NC}")

        # Copy module directories (core/, managers/)
        for module_dir in module_directories:
            copy_directory(current_dir, scripts_dir, module_dir)

        # Copy .env file if it exists in current directory
        env_file_current = current_dir / '.env'
        env_file_target = scripts_dir / '.env'

        if env_file_current.exists():
            shutil.copy2(env_file_current, env_file_target)
            print(f"{GREEN}✓ Copied .env with your API keys{NC}")

        # Copy .env.example if it exists
        env_example = current_dir / '.env.example'
        if env_example.exists():
            shutil.copy2(env_example, scripts_dir / '.env.example')
            print(f"{GREEN}✓ Copied .env.example{NC}")

            # If .env was not copied and doesn't exist, create from example
            if not env_file_current.exists() and not env_file_target.exists():
                shutil.copy2(env_example, env_file_target)
                print(f"{YELLOW}✓ Created .env file from .env.example{NC}")
                print(f"{YELLOW}→ Please edit {env_file_target} and add your API keys{NC}")
        elif not env_file_current.exists():
            print(f"{YELLOW}⚠️  No .env or .env.example file found{NC}")
            print(f"{YELLOW}→ Please create {env_file_target} and add your API keys{NC}")

    # Create batch wrappers for all scripts
    for script_file, command_name in scripts_to_copy:
        script_path = scripts_dir / script_file
        if script_path.exists():
            create_batch_wrapper(script_path, bin_dir / f'{command_name}.bat', command_name)

    # Check PATH
    path_env = os.environ.get('PATH', '')
    bin_path_str = str(bin_dir)

    if bin_path_str not in path_env:
        print(f"\n{YELLOW}⚠️  Add {bin_dir} to your PATH{NC}")
        print(f"1. Press Win + R, type 'sysdm.cpl', press Enter")
        print(f"2. Click 'Environment Variables'")
        print(f"3. Under 'User variables', find 'Path' and click 'Edit'")
        print(f"4. Click 'New' and add: {BLUE}{bin_dir}{NC}")
        print(f"5. Click 'OK' to save")
        print(f"\n{BLUE}Or run in PowerShell as Administrator:{NC}")
        print(f'[Environment]::SetEnvironmentVariable("Path", $env:Path + ";{bin_dir}", "User")')

def setup_unix(system_info):
    """Setup for macOS/Linux"""
    print(f"{YELLOW}Setting up for {system_info['platform']}...{NC}")

    home = system_info['home']
    scripts_dir = home / 'scripts' / 'flutter-tools'
    bin_dir = home / 'bin'

    # Create directories
    scripts_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Define all Python scripts to copy
    scripts_to_copy = [
        ('fdev.py', 'fdev'),
        ('create_page.py', 'create-page'),
        ('gemini_api.py', 'gemini-api'),
        ('git_diff_output_editor.py', 'git-diff-editor')
    ]

    # Define utility files that need to be copied (no command wrappers needed)
    utility_files = ['common_utils.py', 'switch_ai.py', 'requirements.txt']

    # Define module directories to copy
    module_directories = ['core', 'managers']

    # Copy scripts to scripts directory (if not already there)
    current_dir = Path(__file__).parent

    if current_dir != scripts_dir:
        # Copy main scripts
        for script_file, _ in scripts_to_copy:
            if (current_dir / script_file).exists():
                shutil.copy2(current_dir / script_file, scripts_dir / script_file)
                print(f"{GREEN}✓ Copied {script_file}{NC}")

        # Copy utility files
        for util_file in utility_files:
            if (current_dir / util_file).exists():
                shutil.copy2(current_dir / util_file, scripts_dir / util_file)
                print(f"{GREEN}✓ Copied {util_file}{NC}")

        # Copy module directories (core/, managers/)
        for module_dir in module_directories:
            copy_directory(current_dir, scripts_dir, module_dir)

        # Copy .env file if it exists in current directory
        env_file_current = current_dir / '.env'
        env_file_target = scripts_dir / '.env'

        if env_file_current.exists():
            shutil.copy2(env_file_current, env_file_target)
            print(f"{GREEN}✓ Copied .env with your API keys{NC}")

        # Copy .env.example if it exists
        env_example = current_dir / '.env.example'
        if env_example.exists():
            shutil.copy2(env_example, scripts_dir / '.env.example')
            print(f"{GREEN}✓ Copied .env.example{NC}")

            # If .env was not copied and doesn't exist, create from example
            if not env_file_current.exists() and not env_file_target.exists():
                shutil.copy2(env_example, env_file_target)
                print(f"{YELLOW}✓ Created .env file from .env.example{NC}")
                print(f"{YELLOW}→ Please edit {env_file_target} and add your API keys{NC}")
        elif not env_file_current.exists():
            print(f"{YELLOW}⚠️  No .env or .env.example file found{NC}")
            print(f"{YELLOW}→ Please create {env_file_target} and add your API keys{NC}")

    # Make all scripts executable
    for script_file, _ in scripts_to_copy:
        script_path = scripts_dir / script_file
        if script_path.exists():
            os.chmod(script_path, 0o755)

    # Make module files executable too
    for module_dir in ['core', 'managers']:
        module_path = scripts_dir / module_dir
        if module_path.exists():
            for py_file in module_path.glob('*.py'):
                os.chmod(py_file, 0o755)

    # Create shell wrappers with absolute Python path
    # This ensures fdev works correctly even when a venv is activated
    print(f"{BLUE}Creating shell wrappers with Python: {sys.executable}{NC}")
    for script_file, command_name in scripts_to_copy:
        script_path = scripts_dir / script_file
        command_link = bin_dir / command_name

        if script_path.exists():
            # Remove existing symlink or file
            if command_link.exists() or command_link.is_symlink():
                command_link.unlink()
            create_shell_wrapper(script_path, command_link, command_name)

    print(f"{GREEN}✓ Created shell wrappers{NC}")

    # Check PATH
    shell_config = None
    if 'zsh' in os.environ.get('SHELL', ''):
        shell_config = home / '.zshrc'
    elif 'bash' in os.environ.get('SHELL', ''):
        shell_config = home / '.bashrc'

    path_env = os.environ.get('PATH', '')
    bin_path_str = str(bin_dir)

    if bin_path_str not in path_env:
        print(f"\n{YELLOW}⚠️  Add {bin_dir} to your PATH{NC}")
        if shell_config:
            print(f"Add this line to {BLUE}{shell_config}{NC}:")
            print(f'{BLUE}export PATH="$HOME/bin:$PATH"{NC}')
            print(f"\nThen run: {BLUE}source {shell_config}{NC}")
        else:
            print(f"Add {BLUE}{bin_dir}{NC} to your PATH environment variable")

def main():
    print(f"{BLUE}Flutter Tools Cross-Platform Setup{NC}")
    print(f"{BLUE}=================================={NC}\n")

    system_info = get_system_info()
    print(f"Platform: {GREEN}{system_info['platform']}{NC}")
    print(f"Home: {GREEN}{system_info['home']}{NC}")
    print(f"Python: {GREEN}{system_info['python']}{NC}\n")

    # Install required dependencies first
    install_dependencies()

    if system_info['platform'] == 'Windows':
        setup_windows(system_info)
    else:
        setup_unix(system_info)

    print(f"\n{GREEN}🎉 Setup completed!{NC}")
    print(f"\n{BLUE}Available commands:{NC}")
    print(f"  fdev apk                    # Build APK")
    print(f"  fdev setup                  # Full setup")
    print(f"  fdev commit                 # AI-powered commit (uses gemini-api)")
    print(f"  create-page page user_info  # Create page structure")
    print(f"  gemini-api                  # Multi-AI service (Groq/Mistral/SambaNova/OpenRouter)")
    print(f"  git-diff-editor             # Git diff editor with AI prompts")

    print(f"\n{BLUE}Project structure:{NC}")
    print(f"  {GREEN}{system_info['home']}/scripts/flutter-tools/{NC}")
    print(f"    ├── fdev.py               # Main CLI")
    print(f"    ├── core/                 # Constants & state")
    print(f"    └── managers/             # Feature modules")

    print(f"\n{BLUE}AI Configuration:{NC}")
    env_file_path = system_info['home'] / 'scripts' / 'flutter-tools' / '.env'
    print(f"  Edit: {GREEN}{env_file_path}{NC}")
    print(f"  {YELLOW}1. Add your API key for your preferred AI service{NC}")
    print(f"  {YELLOW}2. Set DEFAULT_AI_SERVICE to: groq/mistral/sambanova/openrouter{NC}")
    print(f"  {YELLOW}3. Test with: {BLUE}python3 {system_info['home']}/scripts/flutter-tools/gemini_api.py{NC}")

    if system_info['platform'] == 'Windows':
        print(f"\n{YELLOW}Note: Restart your terminal or Command Prompt to use the commands{NC}")
    else:
        print(f"\n{YELLOW}Note: You may need to restart your terminal or run 'source ~/.zshrc'{NC}")

if __name__ == "__main__":
    main()
