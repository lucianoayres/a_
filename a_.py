#!/usr/bin/env python3
"""
a_ - A simple mouse automation tool

This script moves the mouse cursor to the specified X and Y coordinates
provided as command line arguments.
"""

import sys
import time
import argparse
from pynput.mouse import Controller
import subprocess
import re
import platform


def get_screen_resolution():
    """
    Get the screen resolution based on the operating system.

    Returns:
        tuple: (width, height) of the primary monitor
    """
    system = platform.system()

    if system == "Linux":
        try:
            # Try using xrandr command
            output = subprocess.check_output(["xrandr"], text=True)
            # Look for the primary display
            for line in output.split('\n'):
                if " connected primary " in line:
                    match = re.search(r'(\d+)x(\d+)', line)
                    if match:
                        return int(match.group(1)), int(match.group(2))

            # If primary not found, use the first connected display
            for line in output.split('\n'):
                if " connected " in line:
                    match = re.search(r'(\d+)x(\d+)', line)
                    if match:
                        return int(match.group(1)), int(match.group(2))
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    elif system == "Darwin":  # macOS
        try:
            output = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"], text=True)
            match = re.search(r'Resolution: (\d+) x (\d+)', output)
            if match:
                return int(match.group(1)), int(match.group(2))
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    elif system == "Windows":
        try:
            # Using powershell to get screen resolution
            command = "powershell \"(Get-WmiObject -Class Win32_VideoController).VideoModeDescription\""
            output = subprocess.check_output(command, shell=True, text=True)
            match = re.search(r'(\d+) x (\d+)', output)
            if match:
                return int(match.group(1)), int(match.group(2))
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    # Fallback: Get current mouse position and move it to extreme positions
    mouse = Controller()
    original_pos = mouse.position

    # Try to find screen boundaries by moving to extreme positions
    mouse.position = (100000, 100000)  # Move to a very large position
    max_pos = mouse.position

    # Restore original position
    mouse.position = original_pos

    # If we got some reasonable values
    if max_pos[0] > 100 and max_pos[1] > 100:
        return max_pos

    # Last resort default
    return (1920, 1080)


def move_mouse(x, y, delay=0, check_bounds=True):
    """
    Move the mouse to the specified coordinates.

    Args:
        x (int): X coordinate
        y (int): Y coordinate
        delay (float): Delay in seconds before moving the mouse
        check_bounds (bool): Whether to check if coordinates are within screen bounds
    """
    mouse = Controller()

    if check_bounds:
        screen_width, screen_height = get_screen_resolution()
        print(f"Detected screen resolution: {screen_width}x{screen_height}")

        if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
            print(
                f"Warning: Coordinates ({x}, {y}) are outside screen bounds ({screen_width}x{screen_height})")
            print("Do you want to continue anyway? (y/n)")
            response = input().lower()
            if response != 'y' and response != 'yes':
                print("Operation cancelled.")
                return

    if delay > 0:
        print(f"Waiting for {delay} seconds before moving mouse...")
        time.sleep(delay)

    print(f"Moving mouse to coordinates: ({x}, {y})")
    mouse.position = (x, y)
    print(f"Current mouse position: {mouse.position}")


def main():
    """Parse command line arguments and move the mouse accordingly."""
    parser = argparse.ArgumentParser(
        description='Move the mouse to specified coordinates.')

    # Create a mutually exclusive group for the main commands
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--show-resolution', action='store_true',
                       help='Show screen resolution and exit')

    # Only require x and y if we're not showing resolution
    parser.add_argument('x', type=int, nargs='?',
                        help='X coordinate')
    parser.add_argument('y', type=int, nargs='?',
                        help='Y coordinate')

    # Optional arguments
    parser.add_argument('-d', '--delay', type=float, default=0,
                        help='Delay in seconds before moving the mouse (default: 0)')
    parser.add_argument('--ignore-bounds', action='store_true',
                        help='Ignore screen boundary checks')

    args = parser.parse_args()

    # Show resolution and exit if requested
    if args.show_resolution:
        width, height = get_screen_resolution()
        print(f"Screen resolution: {width}x{height}")
        return

    # If not showing resolution, we need both x and y coordinates
    if args.x is None or args.y is None:
        parser.error(
            "the following arguments are required: x, y (unless --show-resolution is specified)")

    # Move the mouse
    move_mouse(args.x, args.y, args.delay, not args.ignore_bounds)


if __name__ == "__main__":
    main()
