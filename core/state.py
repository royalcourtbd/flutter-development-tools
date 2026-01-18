#!/usr/bin/env python3
"""
Shared state management for flutter-dev tools
"""

# Global variable to store selected Android device
_SELECTED_DEVICE = None


def get_selected_device():
    """Get the currently selected device"""
    global _SELECTED_DEVICE
    return _SELECTED_DEVICE


def set_selected_device(device):
    """Set the selected device"""
    global _SELECTED_DEVICE
    _SELECTED_DEVICE = device


def clear_selected_device():
    """Clear the selected device"""
    global _SELECTED_DEVICE
    _SELECTED_DEVICE = None
