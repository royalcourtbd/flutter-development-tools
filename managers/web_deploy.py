#!/usr/bin/env python3
"""
Web Deploy Manager - Build Flutter web and deploy to Firebase
(backend functions + frontend hosting together)
"""

import subprocess

from common_utils import RED, GREEN, YELLOW, BLUE, NC, timer_decorator
from managers.build import run_flutter_command


@timer_decorator
def web_deploy():
    """Build Flutter web (release) and deploy functions + hosting to Firebase."""
    print(f"{YELLOW}Building Flutter web (release)...{NC}\n")

    build_success = run_flutter_command(
        ["flutter", "build", "web", "--release"],
        "Building web...                                      "
    )

    if not build_success:
        print(f"\n{RED}✗ Web build failed!{NC}")
        return False

    print(f"\n{YELLOW}Deploying to Firebase (functions + hosting)...{NC}\n")

    try:
        result = subprocess.run(
            ["firebase", "deploy", "--only", "functions,hosting"]
        )
    except FileNotFoundError:
        print(f"{RED}✗ 'firebase' CLI not found.{NC}")
        print(f"{YELLOW}Install it with: npm install -g firebase-tools{NC}")
        return False

    if result.returncode != 0:
        print(f"\n{RED}✗ Firebase deploy failed!{NC}")
        return False

    print(f"\n{GREEN}✓ Web deployed successfully (functions + hosting)!{NC}")
    return True
