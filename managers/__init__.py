#!/usr/bin/env python3
"""
Managers module - All manager functions
"""

from .device import (
    get_all_connected_devices,
    select_device_if_multiple,
    build_adb_cmd,
    ensure_device_connected,
    get_usb_devices,
    select_usb_device,
)

from .build import (
    build_apk,
    build_apk_split_per_abi,
    build_aab,
    release_run,
)

from .git import (
    create_and_push_tag,
    smart_commit,
    sync_branches,
)

from .app import (
    install_apk,
    uninstall_app,
    clear_app_data,
    get_current_foreground_app,
)

from .project import (
    full_setup,
    cleanup_project,
    generate_lang,
    run_build_runner,
    repair_cache,
    update_pods,
    create_page,
)

from .mirror import (
    setup_wireless_adb,
    launch_scrcpy,
)
