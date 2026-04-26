#!/usr/bin/env python3
"""
Brew Module - Interactive Homebrew package manager
Browse, inspect, and uninstall packages with full cleanup
"""

import subprocess
import shutil
import sys

from common_utils import RED, GREEN, YELLOW, BLUE, MAGENTA, NC, CHECKMARK, CROSS


def _run_brew(args, timeout=15):
    """Run a brew command and return stdout lines."""
    try:
        result = subprocess.run(
            ["brew"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace',
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ""
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def _get_leaves():
    """Get top-level installed packages (no dependents)."""
    output = _run_brew(["leaves"])
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def _get_all_installed():
    """Get all installed formulae."""
    output = _run_brew(["list", "--formula"])
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def _get_casks():
    """Get all installed casks."""
    output = _run_brew(["list", "--cask"])
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def _get_package_info(package):
    """Get detailed info about a package."""
    info = {}

    # Basic info
    raw = _run_brew(["info", package])
    if raw:
        info['raw_info'] = raw

    # Versions installed
    versions_raw = _run_brew(["list", "--versions", package])
    if versions_raw:
        parts = versions_raw.split()
        info['versions'] = parts[1:] if len(parts) > 1 else []
    else:
        info['versions'] = []

    # Dependencies
    deps_raw = _run_brew(["deps", package])
    info['deps'] = [d.strip() for d in deps_raw.splitlines() if d.strip()] if deps_raw else []

    # Who uses this package (reverse dependencies)
    uses_raw = _run_brew(["uses", "--installed", package])
    info['used_by'] = [u.strip() for u in uses_raw.splitlines() if u.strip()] if uses_raw else []

    # Cache file
    cache_raw = _run_brew(["--cache", package])
    info['cache_path'] = cache_raw.strip() if cache_raw else None

    # Install location
    prefix_raw = _run_brew(["--prefix", package])
    info['location'] = prefix_raw.strip() if prefix_raw else None

    # Cellar location
    cellar_raw = _run_brew(["--cellar", package])
    info['cellar'] = cellar_raw.strip() if cellar_raw else None

    return info


def _display_package_details(package, info):
    """Display detailed package information."""
    print(f"\n{BLUE}{'═' * 54}{NC}")
    print(f"{BLUE}  Package: {GREEN}{package}{NC}")
    print(f"{BLUE}{'═' * 54}{NC}")

    # Versions
    if info['versions']:
        print(f"\n  {YELLOW}Installed Version(s):{NC}")
        for v in info['versions']:
            print(f"    {GREEN}{v}{NC}")
    else:
        print(f"\n  {YELLOW}Version:{NC} {RED}unknown{NC}")

    # Location
    if info.get('location'):
        print(f"\n  {YELLOW}Install Location:{NC}")
        print(f"    {info['location']}")

    if info.get('cellar'):
        print(f"  {YELLOW}Cellar:{NC}")
        print(f"    {info['cellar']}")

    # Dependencies
    if info['deps']:
        print(f"\n  {YELLOW}Dependencies ({len(info['deps'])}):{NC}")
        for dep in info['deps']:
            print(f"    {BLUE}•{NC} {dep}")
    else:
        print(f"\n  {YELLOW}Dependencies:{NC} none")

    # Used by (reverse deps)
    if info['used_by']:
        print(f"\n  {YELLOW}Used By ({len(info['used_by'])}):{NC}")
        for user in info['used_by']:
            print(f"    {MAGENTA}•{NC} {user}")
    else:
        print(f"\n  {YELLOW}Used By:{NC} {GREEN}nobody (safe to remove){NC}")

    # Cache
    if info.get('cache_path'):
        import os
        cache_exists = os.path.exists(info['cache_path'])
        if cache_exists:
            size = os.path.getsize(info['cache_path'])
            size_str = _format_size(size)
            print(f"\n  {YELLOW}Cache:{NC} {size_str}")
            print(f"    {info['cache_path']}")
        else:
            print(f"\n  {YELLOW}Cache:{NC} {GREEN}no cached files{NC}")
    else:
        print(f"\n  {YELLOW}Cache:{NC} {GREEN}no cached files{NC}")

    print(f"\n{BLUE}{'─' * 54}{NC}")


def _format_size(size_bytes):
    """Format bytes into human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _uninstall_package(package, info):
    """Fully uninstall a package with dependencies and cache cleanup."""
    # Warning if others depend on this
    if info['used_by']:
        print(f"\n  {RED}Warning: ei package gulo depend kore '{package}' er upor:{NC}")
        for user in info['used_by']:
            print(f"    {RED}• {user}{NC}")
        print(f"\n  {YELLOW}Uninstall korle oi package gulo break hote pare!{NC}")

    confirm = input(f"\n  {MAGENTA}'{package}' fully remove korte chao? (y/N): {NC}").strip().lower()
    if confirm != 'y':
        print(f"  {YELLOW}Cancelled.{NC}")
        return False

    print()
    success = True

    # Step 1: Uninstall the package
    print(f"  Uninstalling {package}...", end=' ', flush=True)
    result = subprocess.run(
        ["brew", "uninstall", "--zap", package],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"{CHECKMARK}")
    else:
        # Try without --zap (some packages don't support it)
        result = subprocess.run(
            ["brew", "uninstall", package],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"{CHECKMARK}")
        else:
            print(f"{CROSS}")
            print(f"  {RED}{result.stderr.strip()}{NC}")
            success = False

    if not success:
        return False

    # Step 2: Remove unused dependencies
    print(f"  Removing unused dependencies...", end=' ', flush=True)
    result = subprocess.run(
        ["brew", "autoremove"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        removed = [l for l in result.stdout.splitlines() if 'Uninstalling' in l]
        if removed:
            print(f"{CHECKMARK} ({len(removed)} removed)")
            for line in removed:
                pkg = line.replace('Uninstalling', '').strip().split()[0] if line else ""
                print(f"    {BLUE}•{NC} {pkg}")
        else:
            print(f"{CHECKMARK} (none to remove)")
    else:
        print(f"{CROSS}")

    # Step 3: Clean cache
    print(f"  Cleaning cache...", end=' ', flush=True)
    result = subprocess.run(
        ["brew", "cleanup", "--prune=all"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"{CHECKMARK}")
    else:
        print(f"{CROSS}")

    print(f"\n  {GREEN}{CHECKMARK} '{package}' fully removed!{NC}")
    return True


def _clear_package_cache(package, info):
    """Clear cached files for a specific package."""
    import os
    cache_path = info.get('cache_path')

    if not cache_path or not os.path.exists(cache_path):
        print(f"\n  {GREEN}No cache found for '{package}'{NC}")
        return

    size = os.path.getsize(cache_path)
    size_str = _format_size(size)

    confirm = input(f"\n  {MAGENTA}Cache ({size_str}) clear korte chao? (y/N): {NC}").strip().lower()
    if confirm != 'y':
        print(f"  {YELLOW}Cancelled.{NC}")
        return

    try:
        os.remove(cache_path)
        print(f"  {CHECKMARK} Cache cleared! ({size_str} freed)")
    except OSError as e:
        print(f"  {CROSS} {RED}Failed: {e}{NC}")


def _show_package_menu(package, info):
    """Show action menu for a selected package."""
    while True:
        print(f"\n  {YELLOW}Actions:{NC}")
        print(f"    {BLUE}1.{NC} Uninstall (full cleanup)")
        print(f"    {BLUE}2.{NC} Clear cache")
        print(f"    {BLUE}3.{NC} Show raw brew info")
        print(f"    {BLUE}0.{NC} Back to list")

        try:
            choice = input(f"\n  {MAGENTA}Select [0-3]: {NC}").strip()

            if choice == '0' or choice == '':
                return False  # back to list

            elif choice == '1':
                removed = _uninstall_package(package, info)
                if removed:
                    return True  # refresh list

            elif choice == '2':
                _clear_package_cache(package, info)

            elif choice == '3':
                if info.get('raw_info'):
                    print(f"\n{info['raw_info']}")
                else:
                    print(f"\n  {RED}No info available{NC}")

            else:
                print(f"  {RED}Invalid choice{NC}")

        except KeyboardInterrupt:
            print()
            return False
        except EOFError:
            return False


def brew_manager():
    """Interactive Homebrew package manager."""
    # Check if brew is installed
    if not shutil.which("brew"):
        print(f"\n{RED}Homebrew is not installed!{NC}")
        print(f"{YELLOW}Install: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"{NC}")
        return

    while True:
        print(f"\n{BLUE}╔══════════════════════════════════════════════════════╗{NC}")
        print(f"{BLUE}║          fdev brew - Homebrew Package Manager        ║{NC}")
        print(f"{BLUE}╚══════════════════════════════════════════════════════╝{NC}")
        print(f"\n  {YELLOW}View:{NC}")
        print(f"    {BLUE}1.{NC} Top-level packages (brew leaves)")
        print(f"    {BLUE}2.{NC} All installed formulae")
        print(f"    {BLUE}3.{NC} All installed casks (GUI apps)")
        print(f"    {BLUE}4.{NC} Global cleanup (autoremove + cache)")
        print(f"    {BLUE}0.{NC} Exit")

        try:
            mode = input(f"\n  {MAGENTA}Select [0-4]: {NC}").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return

        if mode == '0' or mode == '':
            return
        elif mode == '4':
            _global_cleanup()
            continue
        elif mode == '1':
            packages = _get_leaves()
            list_title = "Top-level Packages (brew leaves)"
        elif mode == '2':
            packages = _get_all_installed()
            list_title = "All Installed Formulae"
        elif mode == '3':
            packages = _get_casks()
            list_title = "All Installed Casks"
        else:
            print(f"  {RED}Invalid choice{NC}")
            continue

        if not packages:
            print(f"\n  {YELLOW}No packages found.{NC}")
            continue

        # Package selection loop
        _package_selection_loop(packages, list_title)


def _package_selection_loop(packages, title):
    """Display numbered package list and handle selection."""
    while True:
        print(f"\n  {YELLOW}{title} ({len(packages)}):{NC}\n")

        # Display in columns for better readability
        col_width = max(len(p) for p in packages) + 4
        cols = max(1, 54 // col_width)

        for i, pkg in enumerate(packages, 1):
            num = f"{i}.".ljust(4)
            entry = f"    {BLUE}{num}{NC}{pkg.ljust(col_width)}"
            if cols > 1 and i % cols != 0:
                print(entry, end='')
            else:
                print(entry)

        # Handle trailing newline for incomplete rows
        if len(packages) % cols != 0 and cols > 1:
            print()

        print(f"\n  {YELLOW}0.{NC} Back")

        try:
            choice = input(f"\n  {MAGENTA}Select package [0-{len(packages)}]: {NC}").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return

        if choice == '0' or choice == '':
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(packages):
                selected = packages[index]
                print(f"\n  {GREEN}✓ Selected: {selected}{NC}")
                print(f"  Loading info...", end=' ', flush=True)

                info = _get_package_info(selected)
                print(f"{CHECKMARK}")

                _display_package_details(selected, info)
                refresh = _show_package_menu(selected, info)

                if refresh:
                    # Package was removed, refresh list
                    return
            else:
                print(f"  {RED}Invalid choice. Enter 1-{len(packages)}{NC}")
        except ValueError:
            print(f"  {RED}Invalid input. Enter a number{NC}")


def _global_cleanup():
    """Run global brew cleanup (autoremove + cache prune)."""
    print(f"\n  {YELLOW}Global Cleanup:{NC}\n")

    confirm = input(f"  {MAGENTA}Unused dependencies remove + cache clean korte chao? (y/N): {NC}").strip().lower()
    if confirm != 'y':
        print(f"  {YELLOW}Cancelled.{NC}")
        return

    print()

    # Autoremove
    print(f"  Removing unused dependencies...", end=' ', flush=True)
    result = subprocess.run(
        ["brew", "autoremove"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        removed = [l for l in result.stdout.splitlines() if 'Uninstalling' in l]
        if removed:
            print(f"{CHECKMARK} ({len(removed)} removed)")
            for line in removed:
                parts = line.split()
                pkg = parts[1] if len(parts) > 1 else line
                print(f"    {BLUE}•{NC} {pkg}")
        else:
            print(f"{CHECKMARK} (nothing to remove)")
    else:
        print(f"{CROSS}")

    # Cache cleanup
    print(f"  Cleaning cache...", end=' ', flush=True)
    result = subprocess.run(
        ["brew", "cleanup", "--prune=all", "-s"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"{CHECKMARK}")
    else:
        print(f"{CROSS}")

    # Show disk usage
    cache_raw = _run_brew(["--cache"])
    if cache_raw:
        import os
        cache_dir = cache_raw.strip()
        if os.path.isdir(cache_dir):
            total = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, filenames in os.walk(cache_dir)
                for f in filenames
            )
            print(f"\n  {GREEN}Remaining cache size: {_format_size(total)}{NC}")

    print(f"\n  {GREEN}{CHECKMARK} Cleanup done!{NC}")
