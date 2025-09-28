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
    with open(wrapper_path, 'w') as f:
        f.write(batch_content)
    print(f"{GREEN}✓ Created Windows batch wrapper: {wrapper_path}{NC}")

def create_shell_wrapper(script_path, wrapper_path, script_name):
    """Create Unix shell wrapper"""
    shell_content = f'''#!/bin/bash
"{sys.executable}" "{script_path}" "$@"
'''
    with open(wrapper_path, 'w') as f:
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
    
    # Copy scripts to scripts directory (if not already there)
    current_dir = Path(__file__).parent
    flutter_dev_script = scripts_dir / 'flutter-dev.py'
    create_page_script = scripts_dir / 'create_page.py'
    
    if current_dir != scripts_dir:
        if (current_dir / 'flutter-dev.py').exists():
            shutil.copy2(current_dir / 'flutter-dev.py', flutter_dev_script)
        if (current_dir / 'create_page.py').exists():
            shutil.copy2(current_dir / 'create_page.py', create_page_script)
    
    # Create batch wrappers
    create_batch_wrapper(flutter_dev_script, bin_dir / 'flutter-dev.bat', 'flutter-dev')
    create_batch_wrapper(create_page_script, bin_dir / 'create-page.bat', 'create-page')
    
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
    
    # Copy scripts to scripts directory (if not already there)
    current_dir = Path(__file__).parent
    flutter_dev_script = scripts_dir / 'flutter-dev.py'
    create_page_script = scripts_dir / 'create_page.py'
    
    if current_dir != scripts_dir:
        if (current_dir / 'flutter-dev.py').exists():
            shutil.copy2(current_dir / 'flutter-dev.py', flutter_dev_script)
        if (current_dir / 'create_page.py').exists():
            shutil.copy2(current_dir / 'create_page.py', create_page_script)
    
    # Make scripts executable
    os.chmod(flutter_dev_script, 0o755)
    os.chmod(create_page_script, 0o755)
    
    # Create symlinks (preferred) or shell wrappers
    flutter_dev_link = bin_dir / 'flutter-dev'
    create_page_link = bin_dir / 'create-page'
    
    try:
        # Try symlinks first
        if flutter_dev_link.exists() or flutter_dev_link.is_symlink():
            flutter_dev_link.unlink()
        flutter_dev_link.symlink_to(flutter_dev_script)
        
        if create_page_link.exists() or create_page_link.is_symlink():
            create_page_link.unlink()
        create_page_link.symlink_to(create_page_script)
        
        print(f"{GREEN}✓ Created symlinks{NC}")
        
    except (OSError, NotImplementedError):
        # Fallback to shell wrappers
        print(f"{YELLOW}Symlinks not available, creating shell wrappers...{NC}")
        create_shell_wrapper(flutter_dev_script, flutter_dev_link, 'flutter-dev')
        create_shell_wrapper(create_page_script, create_page_link, 'create-page')
    
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
    
    # Update flutter-dev.py
    flutter_dev_path = Path.home() / 'scripts' / 'flutter-tools' / 'flutter-dev.py'
    if flutter_dev_path.exists():
        with open(flutter_dev_path, 'r') as f:
            content = f.read()
        
        # Replace hardcoded path with cross-platform version
        old_path = 'os.path.expanduser("~/scripts/flutter-tools/create_page.py")'
        new_path = 'str(Path.home() / "scripts" / "flutter-tools" / "create_page.py")'
        
        if old_path in content and 'from pathlib import Path' not in content:
            # Add Path import
            content = content.replace('import os', 'import os\nfrom pathlib import Path')
            # Replace path
            content = content.replace(old_path, new_path)
            
            with open(flutter_dev_path, 'w') as f:
                f.write(content)
            
            print(f"{GREEN}✓ Updated flutter-dev.py for cross-platform paths{NC}")

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
    
    print(f"\\n{GREEN}🎉 Setup completed!{NC}")
    print(f"\n{BLUE}Available commands:{NC}")
    print(f"  flutter-dev apk             # Build APK")
    print(f"  flutter-dev setup           # Full setup")
    print(f"  create-page page user_info  # Create page structure")
    
    print(f"\\n{BLUE}Master files location:{NC}")
    print(f"  {GREEN}{system_info['home']}/scripts/flutter-tools/{NC}")
    
    if system_info['platform'] == 'Windows':
        print(f"\\n{YELLOW}Note: Restart your terminal or Command Prompt to use the commands{NC}")
    else:
        print(f"\\n{YELLOW}Note: You may need to restart your terminal or run 'source ~/.zshrc'{NC}")

if __name__ == "__main__":
    main()
