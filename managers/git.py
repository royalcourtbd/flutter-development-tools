#!/usr/bin/env python3
"""
Git Manager - Git tag, commit, version functions
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from common_utils import (
    RED, GREEN, YELLOW, BLUE, NC,
    timer_decorator,
    is_windows,
)
from core.constants import PATTERNS
from managers.build import run_flutter_command


def get_version_from_pubspec():
    """Get the version from pubspec.yaml using regex"""
    if os.path.isfile("pubspec.yaml"):
        with open("pubspec.yaml", 'r', encoding='utf-8') as file:
            try:
                content = file.read()
                # Use regex to find the version field in pubspec.yaml
                version_match = PATTERNS['version'].search(content)
                if version_match:
                    version = version_match.group(1).strip()
                    # Remove quotes if present and split by + to get only version number
                    version = version.strip('"\'').split('+')[0]
                    return version
                else:
                    print(f"{RED}Error: Could not find 'version' field in pubspec.yaml.{NC}")
                    return None
            except Exception as e:
                print(f"{RED}Error: Could not read pubspec.yaml: {e}{NC}")
                return None
    else:
        print(f"{RED}Error: pubspec.yaml not found in the current directory.{NC}")
        print(f"Please run this command from the root of a Flutter project.")
        return None


def parse_version(version_str):
    """Parse version string (e.g., 'v1.2.3' or '1.2.3') into tuple (1, 2, 3)"""
    # Remove 'v' prefix if present
    version_str = version_str.lstrip('v')
    try:
        parts = version_str.split('.')
        return tuple(int(p) for p in parts[:3])  # Return only major.minor.patch
    except:
        return None


def get_all_tags():
    """Get all tags from both local and remote repositories"""
    all_tags = set()

    # Get local tags
    try:
        result = subprocess.run(["git", "tag", "-l"],
                              capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.stdout.strip():
            local_tags = result.stdout.strip().split('\n')
            all_tags.update(local_tags)
    except Exception as e:
        print(f"{YELLOW}Warning: Could not get local tags: {e}{NC}")

    # Get remote tags
    try:
        result = subprocess.run(["git", "ls-remote", "--tags", "origin"],
                              capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                # Extract tag name from "hash refs/tags/v1.0.0"
                if 'refs/tags/' in line:
                    tag = line.split('refs/tags/')[-1]
                    # Skip ^{} references
                    if not tag.endswith('^{}'):
                        all_tags.add(tag)
    except Exception as e:
        print(f"{YELLOW}Warning: Could not get remote tags: {e}{NC}")

    return sorted(all_tags)


def increment_version(version_tuple):
    """Increment patch version: (1, 2, 3) -> (1, 2, 4)"""
    major, minor, patch = version_tuple
    return (major, minor, patch + 1)


def get_build_number_from_pubspec():
    """Get the build number from pubspec.yaml (e.g., from '1.0.0+5' returns 5)"""
    if os.path.isfile("pubspec.yaml"):
        with open("pubspec.yaml", 'r', encoding='utf-8') as file:
            try:
                content = file.read()
                # Find version line with build number
                version_match = PATTERNS['version_with_build'].search(content)
                if version_match:
                    build_number = int(version_match.group(2))
                    return build_number
                return None
            except Exception:
                return None
    return None


def update_pubspec_version(new_version):
    """Update version in pubspec.yaml file, preserving and incrementing build number
    Returns: (success, build_number) tuple
    """
    if not os.path.isfile("pubspec.yaml"):
        print(f"{RED}Error: pubspec.yaml not found in the current directory.{NC}")
        return (False, None)

    try:
        with open("pubspec.yaml", 'r', encoding='utf-8') as file:
            content = file.read()

        # Get current build number
        current_build = get_build_number_from_pubspec()

        # Increment build number or start from 1
        new_build = (current_build + 1) if current_build is not None else 1

        # Create new version string with build number
        new_version_with_build = f"{new_version}+{new_build}"

        # Find the version line and replace it
        new_content = PATTERNS['version_line'].sub(
            f'version: {new_version_with_build}',
            content
        )

        # Write back to file
        with open("pubspec.yaml", 'w', encoding='utf-8') as file:
            file.write(new_content)

        print(f"{GREEN}  Build number: {current_build or 0} → {new_build}{NC}")
        return (True, new_build)
    except Exception as e:
        print(f"{RED}Error updating pubspec.yaml: {e}{NC}")
        return (False, None)


def commit_version_change(version, build_number=None):
    """Commit the pubspec.yaml version change"""
    # Add pubspec.yaml to staging
    result = subprocess.run(
        ["git", "add", "pubspec.yaml"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    if result.returncode != 0:
        print(f"{RED}Failed to stage pubspec.yaml{NC}")
        return False

    # Commit with version bump message
    if build_number:
        commit_message = f"chore: bump version to {version}+{build_number}"
    else:
        commit_message = f"chore: bump version to {version}"

    result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    if result.returncode != 0:
        print(f"{RED}Failed to commit version change{NC}")
        return False

    return True


def create_and_push_tag():
    """Create git tag by auto-incrementing the latest existing tag and push to remote"""
    print(f"{YELLOW}Creating and pushing git tag...{NC}\n")

    # Get all existing tags
    print(f"{BLUE}Checking existing tags...{NC}")
    all_tags = get_all_tags()

    if all_tags:
        print(f"{GREEN}Found {len(all_tags)} existing tag(s):{NC}")
        for tag in all_tags[-5:]:  # Show last 5 tags
            print(f"  • {tag}")
        if len(all_tags) > 5:
            print(f"  ... and {len(all_tags) - 5} more")
        print()

    # Find the latest version
    latest_version = None
    latest_tag = None

    for tag in all_tags:
        parsed = parse_version(tag)
        if parsed:
            if latest_version is None or parsed > latest_version:
                latest_version = parsed
                latest_tag = tag

    # Determine new version
    if latest_version:
        new_version = increment_version(latest_version)
        new_tag = f"v{new_version[0]}.{new_version[1]}.{new_version[2]}"
        new_version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
        print(f"{BLUE}Latest tag: {latest_tag} → New tag: {new_tag}{NC}\n")
    else:
        # No existing tags, use version from pubspec
        version = get_version_from_pubspec()
        if not version:
            print(f"{YELLOW}No existing tags found and cannot read pubspec version.{NC}")
            print(f"{YELLOW}Using default: v1.0.0{NC}\n")
            new_tag = "v1.0.0"
            new_version_str = "1.0.0"
        else:
            new_tag = f"v{version}"
            new_version_str = version
            print(f"{BLUE}No existing tags found. Creating first tag: {new_tag}{NC}\n")

    # Confirm with user
    user_input = input(f"Update pubspec.yaml, commit and create tag {GREEN}{new_tag}{NC}? (Y/n): ")
    if user_input.lower() == 'n':
        print(f"{YELLOW}Operation cancelled.{NC}")
        return False

    # Step 1: Update pubspec.yaml version
    print(f"{BLUE}Updating pubspec.yaml version to {new_version_str}...{NC}")
    success, build_number = update_pubspec_version(new_version_str)
    if not success:
        print(f"{RED}Failed to update pubspec.yaml{NC}")
        return False
    print(f"{GREEN}✓ pubspec.yaml updated to {new_version_str}+{build_number}{NC}")

    # Step 2: Commit the version change
    print(f"{BLUE}Committing version change...{NC}")
    if not commit_version_change(new_version_str, build_number):
        print(f"{RED}Failed to commit version change{NC}")
        return False
    print(f"{GREEN}✓ Version change committed{NC}")

    # Step 3: Create git tag
    success = run_flutter_command(["git", "tag", new_tag], f"Creating tag {new_tag}...                             ")
    if not success:
        print(f"{RED}Failed to create git tag.{NC}")
        return False

    # Step 4: Push commit to remote
    print(f"{BLUE}Pushing commit to remote...{NC}")
    success = run_flutter_command(["git", "push"], f"Pushing commit...                                   ")
    if not success:
        print(f"{RED}Failed to push commit to remote.{NC}")
        return False

    # Step 5: Push tag to remote
    success = run_flutter_command(["git", "push", "-u", "origin", new_tag], f"Pushing tag to remote...                            ")
    if not success:
        print(f"{RED}Failed to push tag to remote.{NC}")
        return False

    print(f"\n{GREEN}✓ Version {new_version_str}+{build_number} updated, committed, and git tag {new_tag} created and pushed successfully!{NC}")
    return True


def discard_changes(discard_all=True):
    """Discard all uncommitted changes in the current git repository

    Args:
        discard_all: If True, also removes untracked files (git clean -fd)
    """
    print(f"{YELLOW}Discarding uncommitted changes...{NC}\n")

    # Check if git repository
    try:
        subprocess.run(["git", "status"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print(f"{RED}Error: Not a git repository or git not available{NC}")
        return False

    # Check for changes
    try:
        # Get tracked file changes
        result = subprocess.run(["git", "status", "--porcelain"],
                              capture_output=True, text=True, encoding='utf-8', errors='replace')
        changes = result.stdout.strip()

        if not changes:
            print(f"{GREEN}No uncommitted changes to discard{NC}")
            return True

        # Parse and display changes
        modified_files = []
        untracked_files = []

        for line in changes.split('\n'):
            if line:
                status = line[:2]
                filename = line[3:]
                if status.strip() == '??':
                    untracked_files.append(filename)
                else:
                    modified_files.append(filename)

        # Show what will be discarded
        if modified_files:
            print(f"{BLUE}Modified/Staged files to reset ({len(modified_files)}):{NC}")
            for f in modified_files[:10]:
                print(f"  {RED}✗{NC} {f}")
            if len(modified_files) > 10:
                print(f"  ... and {len(modified_files) - 10} more")
            print()

        if untracked_files and discard_all:
            print(f"{BLUE}Untracked files to delete ({len(untracked_files)}):{NC}")
            for f in untracked_files[:10]:
                print(f"  {RED}✗{NC} {f}")
            if len(untracked_files) > 10:
                print(f"  ... and {len(untracked_files) - 10} more")
            print()

        # Ask for confirmation
        total = len(modified_files) + (len(untracked_files) if discard_all else 0)
        print(f"{YELLOW}⚠ WARNING: This action cannot be undone!{NC}")
        user_input = input(f"Discard {total} file(s)? (Y/n): ")

        if user_input.lower() == 'n':
            print(f"{YELLOW}Operation cancelled{NC}")
            return False

        # Reset tracked file changes
        if modified_files:
            print(f"{BLUE}Resetting tracked files...{NC}")
            result = subprocess.run(["git", "checkout", "."],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode != 0:
                print(f"{RED}Error resetting tracked files: {result.stderr}{NC}")
                return False

            # Also reset staged changes
            subprocess.run(["git", "reset", "HEAD"],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
            print(f"{GREEN}✓ Tracked files reset{NC}")

        # Remove untracked files if requested
        if untracked_files and discard_all:
            print(f"{BLUE}Removing untracked files...{NC}")
            result = subprocess.run(["git", "clean", "-fd"],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode != 0:
                print(f"{RED}Error removing untracked files: {result.stderr}{NC}")
                return False
            print(f"{GREEN}✓ Untracked files removed{NC}")

        print(f"\n{GREEN}✓ All uncommitted changes discarded successfully!{NC}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"{RED}Error checking git changes: {e}{NC}")
        return False


@timer_decorator
def smart_commit():
    """Generate git diff, create commit message using Gemini AI, and commit"""
    print(f"{YELLOW}Smart Git Commit...{NC}\n")

    current_dir = os.getcwd()

    # Check if git repository
    try:
        subprocess.run(["git", "status"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print(f"{RED}Error: Not a git repository or git not available{NC}")
        return False

    # Check for changes
    try:
        result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True, encoding='utf-8', errors='replace')
        staged_changes = result.stdout.strip()

        result = subprocess.run(["git", "diff"], capture_output=True, text=True, encoding='utf-8', errors='replace')
        unstaged_changes = result.stdout.strip()

        if not staged_changes and not unstaged_changes:
            print(f"{YELLOW}No changes detected to commit{NC}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"{RED}Error checking git changes: {e}{NC}")
        return False

    # Get all changes (staged + unstaged)
    try:
        result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True, encoding='utf-8', errors='replace')
        all_changes = result.stdout.strip()

        if not all_changes:
            # If no changes from HEAD, get staged changes only
            all_changes = staged_changes

    except subprocess.CalledProcessError:
        all_changes = staged_changes + "\n" + unstaged_changes

    if not all_changes:
        print(f"{YELLOW}No changes to analyze{NC}")
        return False

    # Import Gemini API
    try:
        script_dir = Path(__file__).parent
        gemini_script = Path.home() / "scripts" / "flutter-tools" / "gemini_api.py"

        if not gemini_script.exists():
            print(f"{RED}Error: gemini_api.py not found{NC}")
            return False

        # Import the function
        sys.path.insert(0, str(Path.home() / "scripts" / "flutter-tools"))
        from gemini_api import generate_commit_message

    except ImportError as e:
        print(f"{RED}Error importing Gemini API: {e}{NC}")
        return False

    # Generate commit message
    commit_message = generate_commit_message(all_changes)

    if not commit_message:
        print(f"{RED}Failed to generate commit message{NC}")
        return False

    print(f"\n{BLUE}Generated commit message:{NC}")

    # Process commit message to add "-" to description lines
    lines = commit_message.split('\n')
    processed_lines = []

    for i, line in enumerate(lines):
        # Skip the first line (title) and empty lines
        if i == 0 or line.strip() == "":
            processed_lines.append(line)
        else:
            # Add "-" to non-empty description lines
            if line.strip():
                processed_lines.append(f"- {line}")
            else:
                processed_lines.append(line)

    formatted_commit_message = '\n'.join(processed_lines)
    print(f"{GREEN}{formatted_commit_message}{NC}\n")

    # Ask for confirmation
    user_input = input(f"Proceed with this commit? (y/N): ")
    if user_input.lower() != 'y':
        print(f"{YELLOW}Commit cancelled{NC}")
        return False

    # Stage all changes if there are unstaged changes
    if unstaged_changes:
        print(f"{YELLOW}Staging all changes...{NC}")
        try:
            subprocess.run(["git", "add", "."], check=True)
            print(f"{GREEN}✓ Changes staged{NC}")
        except subprocess.CalledProcessError as e:
            print(f"{RED}Error staging changes: {e}{NC}")
            return False

    # Commit with generated message
    try:
        subprocess.run(["git", "commit", "-m", formatted_commit_message], check=True)
        print(f"\n{GREEN}✓ Commit successful!{NC}")

        # Wait 1.5 seconds to show success message
        time.sleep(1.5)

        # Clear terminal after successful commit
        if is_windows():
            os.system('cls')
        else:
            os.system('clear')

        print(f"{GREEN}✓ Commit completed and terminal cleared!{NC}")
        print(f"{BLUE}Ready for next commit 🚀{NC}\n")

        return True

    except subprocess.CalledProcessError as e:
        print(f"{RED}Error creating commit: {e}{NC}")
        return False
