#!/usr/bin/env python3
"""
Cross-platform setup script for Flutter development tools
Works on macOS, Linux, and Windows
"""

import os
import sys
import platform
import shutil
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

def create_batch_wrapper(script_path, wrapper_path, script_name):
    """Create Windows batch wrapper"""
    batch_content = f'''@echo off
"{sys.executable}" "{script_path}" %*
'''
    with open(wrapper_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    print(f"{GREEN}✓ Created Windows batch wrapper: {wrapper_path}{NC}")

def create_shell_wrapper(script_path, wrapper_path, script_name):
    """Create Unix shell wrapper"""
    shell_content = f'''#!/bin/bash
"{sys.executable}" "{script_path}" "$@"
'''
    with open(wrapper_path, 'w', encoding='utf-8') as f:
        f.write(shell_content)
    
    # Make executable
    os.chmod(wrapper_path, 0o755)
    print(f"{GREEN}✓ Created shell wrapper: {wrapper_path}{NC}")

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
    
    # Copy scripts to scripts directory (if not already there)
    current_dir = Path(__file__).parent
    
    if current_dir != scripts_dir:
        for script_file, _ in scripts_to_copy:
            if (current_dir / script_file).exists():
                shutil.copy2(current_dir / script_file, scripts_dir / script_file)
                print(f"{GREEN}✓ Copied {script_file}{NC}")
    
    # Create batch wrappers for all scripts
    for script_file, command_name in scripts_to_copy:
        script_path = scripts_dir / script_file
        if script_path.exists():
            create_batch_wrapper(script_path, bin_dir / f'{command_name}.bat', command_name)
    
    # Check PATH
    path_env = os.environ.get('PATH', '')
    bin_path_str = str(bin_dir)
    
    if bin_path_str not in path_env:
        print(f"\\n{YELLOW}⚠️  Add {bin_dir} to your PATH{NC}")
        print(f"1. Press Win + R, type 'sysdm.cpl', press Enter")
        print(f"2. Click 'Environment Variables'")
        print(f"3. Under 'User variables', find 'Path' and click 'Edit'")
        print(f"4. Click 'New' and add: {BLUE}{bin_dir}{NC}")
        print(f"5. Click 'OK' to save")
        print(f"\\n{BLUE}Or run in PowerShell as Administrator:{NC}")
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
    
    # Copy scripts to scripts directory (if not already there)
    current_dir = Path(__file__).parent
    
    if current_dir != scripts_dir:
        for script_file, _ in scripts_to_copy:
            if (current_dir / script_file).exists():
                shutil.copy2(current_dir / script_file, scripts_dir / script_file)
                print(f"{GREEN}✓ Copied {script_file}{NC}")
    
    # Make all scripts executable
    for script_file, _ in scripts_to_copy:
        script_path = scripts_dir / script_file
        if script_path.exists():
            os.chmod(script_path, 0o755)
    
    # Create symlinks (preferred) or shell wrappers
    try:
        # Try symlinks first
        for script_file, command_name in scripts_to_copy:
            script_path = scripts_dir / script_file
            command_link = bin_dir / command_name
            
            if script_path.exists():
                if command_link.exists() or command_link.is_symlink():
                    command_link.unlink()
                command_link.symlink_to(script_path)
        
        print(f"{GREEN}✓ Created symlinks{NC}")
        
    except (OSError, NotImplementedError):
        # Fallback to shell wrappers
        print(f"{YELLOW}Symlinks not available, creating shell wrappers...{NC}")
        for script_file, command_name in scripts_to_copy:
            script_path = scripts_dir / script_file
            command_link = bin_dir / command_name
            
            if script_path.exists():
                create_shell_wrapper(script_path, command_link, command_name)
    
    # Check PATH
    shell_config = None
    if 'zsh' in os.environ.get('SHELL', ''):
        shell_config = home / '.zshrc'
    elif 'bash' in os.environ.get('SHELL', ''):
        shell_config = home / '.bashrc'
    
    path_env = os.environ.get('PATH', '')
    bin_path_str = str(bin_dir)
    
    if bin_path_str not in path_env:
        print(f"\\n{YELLOW}⚠️  Add {bin_dir} to your PATH{NC}")
        if shell_config:
            print(f"Add this line to {BLUE}{shell_config}{NC}:")
            print(f'{BLUE}export PATH="$HOME/bin:$PATH"{NC}')
            print(f"\\nThen run: {BLUE}source {shell_config}{NC}")
        else:
            print(f"Add {BLUE}{bin_dir}{NC} to your PATH environment variable")

def update_scripts_for_cross_platform():
    """Update scripts to be more cross-platform friendly"""
    print(f"{YELLOW}Updating scripts for cross-platform compatibility...{NC}")
    
    # Update fdev.py
    fdev_path = Path.home() / 'scripts' / 'flutter-tools' / 'fdev.py'
    if fdev_path.exists():
        with open(fdev_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace hardcoded path with cross-platform version
        old_path = 'os.path.expanduser("~/scripts/flutter-tools/create_page.py")'
        new_path = 'str(Path.home() / "scripts" / "flutter-tools" / "create_page.py")'
        
        if old_path in content and 'from pathlib import Path' not in content:
            # Add Path import
            content = content.replace('import os', 'import os\nfrom pathlib import Path')
            # Replace path
            content = content.replace(old_path, new_path)
            
            with open(fdev_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"{GREEN}✓ Updated fdev.py for cross-platform paths{NC}")

def main():
    print(f"{BLUE}Flutter Tools Cross-Platform Setup{NC}")
    print(f"{BLUE}=================================={NC}\\n")
    
    system_info = get_system_info()
    print(f"Platform: {GREEN}{system_info['platform']}{NC}")
    print(f"Home: {GREEN}{system_info['home']}{NC}")
    print(f"Python: {GREEN}{system_info['python']}{NC}\\n")
    
    if system_info['platform'] == 'Windows':
        setup_windows(system_info)
    else:
        setup_unix(system_info)
    
    # Update scripts for cross-platform compatibility
    update_scripts_for_cross_platform()
    
    print(f"\n{GREEN}🎉 Setup completed!{NC}")
    print(f"\n{BLUE}Available commands:{NC}")
    print(f"  fdev apk                    # Build APK")
    print(f"  fdev setup                  # Full setup")
    print(f"  create-page page user_info  # Create page structure")
    print(f"  gemini-api                  # Generate AI commit messages")
    print(f"  git-diff-editor             # Git diff editor with AI prompts")
    
    print(f"\\n{BLUE}Master files location:{NC}")
    print(f"  {GREEN}{system_info['home']}/scripts/flutter-tools/{NC}")
    
    if system_info['platform'] == 'Windows':
        print(f"\\n{YELLOW}Note: Restart your terminal or Command Prompt to use the commands{NC}")
    else:
        print(f"\\n{YELLOW}Note: You may need to restart your terminal or run 'source ~/.zshrc'{NC}")

if __name__ == "__main__":
    main()
