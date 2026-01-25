#!/usr/bin/env python3
"""
fdev - Flutter Development CLI Tool
Main entry point and command dispatcher
"""

import os
import sys
import signal

from common_utils import RED, GREEN, YELLOW, BLUE, NC

# Import managers
from managers.build import (
    build_apk,
    build_apk_split_per_abi,
    build_aab,
    release_run,
)
from managers.git import (
    create_and_push_tag,
    smart_commit,
    discard_changes,
    sync_branches,
    deploy_to_deployment,
)
from managers.app import (
    install_apk,
    uninstall_app,
    clear_app_data,
)
from managers.project import (
    full_setup,
    cleanup_project,
    generate_lang,
    run_build_runner,
    repair_cache,
    update_pods,
    create_page,
)
from managers.mirror import (
    setup_wireless_adb,
    launch_scrcpy,
)
from managers.merge import (
    merge_files,
)


def show_usage():
    """Show usage information"""
    print(f"{YELLOW}Usage: {sys.argv[0]} [command] [options]{NC}")
    print(f"\n{BLUE}Build Commands:{NC}")
    print("  apk          Build release APK (Full Process)")
    print("  apk-split    Build APK with --split-per-abi")
    print("  aab          Build release AAB")
    print("  release-run  Build & install release APK on connected device")

    print(f"\n{BLUE}Development Commands:{NC}")
    print("  lang         Generate localization files")
    print("  db           Run build_runner")
    print("  setup        Perform full project setup")
    print("  cleanup      Clean project and get dependencies")
    print("  cache-repair Repair pub cache")
    print("  page         Create page structure (usage: fdev page <page_name>)")

    print(f"\n{BLUE}Device Commands:{NC}")
    print("  install      Install built APK on connected device")
    print("  uninstall    Uninstall app from connected device")
    print("  clear-data   Clear data of currently running foreground app")
    print("  mirror       Launch scrcpy screen mirror (auto-detect device)")
    print("    --wireless Setup wireless ADB connection")

    print(f"\n{BLUE}Git & iOS Commands:{NC}")
    print("  pod          Update iOS pods (macOS/Linux only)")
    print("  tag          Create and push git tag (auto-increment)")
    print("  commit       Smart git commit with AI-generated message")
    print("  discard      Discard all uncommitted changes (tracked + untracked)")
    print("  sync         Sync current branch with other branches bidirectionally")
    print("  deploy       Deploy current branch to 'deployment' branch")

    print(f"\n{BLUE}Utility Commands:{NC}")
    print("  merge        Merge files from paths.txt into single output file")

    print(f"\n{BLUE}Examples:{NC}")
    print(f"  {GREEN}fdev mirror{NC}                    # Launch screen mirror")
    print(f"  {GREEN}fdev mirror --wireless{NC}         # Setup wireless ADB first")
    print(f"  {GREEN}fdev uninstall{NC}                 # Uninstall app (auto-selects device)")
    print(f"  {GREEN}fdev discard{NC}                   # Discard all uncommitted changes")
    print(f"  {GREEN}fdev sync dev-farhan dev-sufi{NC}  # Sync with multiple branches")
    print(f"  {GREEN}fdev deploy{NC}                    # Deploy to deployment branch")

    print(f"\n{BLUE}Note:{NC}")
    print(f"  {YELLOW}Multiple devices detected?{NC} Tool will prompt you to select one.")
    sys.exit(1)


def main():
    """Main function - Command dispatcher"""
    # Create required directories if they don't exist
    os.makedirs("build/app/outputs/flutter-apk", exist_ok=True)
    os.makedirs("build/app/outputs/bundle/release", exist_ok=True)

    if len(sys.argv) < 2:
        show_usage()

    command = sys.argv[1].lower()

    # Build commands
    if command == "apk":
        build_apk()
    elif command == "apk-split":
        build_apk_split_per_abi()
    elif command == "aab":
        build_aab()
    elif command == "release-run":
        release_run()

    # Development commands
    elif command == "lang":
        generate_lang()
    elif command == "db":
        run_build_runner()
    elif command == "setup":
        full_setup()
    elif command == "cache-repair":
        repair_cache()
    elif command == "cleanup":
        cleanup_project()

    # Device commands
    elif command == "install":
        install_apk()
    elif command == "uninstall":
        uninstall_app()
    elif command == "clear-data":
        clear_app_data()

    # Git & iOS commands
    elif command == "pod":
        update_pods()
    elif command == "tag":
        create_and_push_tag()
    elif command == "commit":
        smart_commit()
    elif command == "discard":
        discard_changes(discard_all=True)
    elif command == "sync":
        if len(sys.argv) < 3:
            print(f"{RED}Error: At least one branch name is required.{NC}")
            print(f"{BLUE}Usage: fdev sync <branch1> [branch2] [branch3] ...{NC}")
            print(f"\n{BLUE}Example:{NC}")
            print(f"  {GREEN}fdev sync dev-farhan dev-sufi{NC}")
            sys.exit(1)
        branch_names = sys.argv[2:]
        sync_branches(branch_names)
    elif command == "deploy":
        deploy_to_deployment()

    # Mirror command
    elif command == "mirror":
        # Check for wireless option
        wireless = "--wireless" in sys.argv
        if wireless:
            setup_wireless_adb()
        else:
            launch_scrcpy()

    # Page generation
    elif command == "page":
        if len(sys.argv) < 3:
            print(f"{RED}Error: Page name is required.{NC}")
            print(f"{BLUE}Usage: {sys.argv[0]} page <page_name>{NC}")
            sys.exit(1)
        create_page(sys.argv[2])

    # Utility commands
    elif command == "merge":
        merge_files()

    else:
        show_usage()


if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print(f"\n{YELLOW}Process interrupted. Exiting...{NC}")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    main()
