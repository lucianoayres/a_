#!/usr/bin/env python3
"""
a_ - A simple mouse automation tool

This script moves the mouse cursor to the specified X and Y coordinates
provided as command line arguments.
"""

import sys
import time
import argparse
import math
from pynput.mouse import Controller, Button, Listener
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


def monitor_mouse_position(update_interval=0.1, show_clicks=True, duration=None):
    """
    Monitor and display the current mouse position in real-time.

    Args:
        update_interval (float): Time between position updates in seconds
        show_clicks (bool): Whether to show mouse click events
        duration (float): How long to monitor in seconds (None for indefinite)
    """
    mouse = Controller()
    start_time = time.time()
    click_count = {'left': 0, 'right': 0}

    def on_click(x, y, button, pressed):
        if pressed:
            btn_name = 'left' if button == Button.left else 'right' if button == Button.right else 'middle'
            click_count[btn_name if btn_name in click_count else 'other'] = click_count.get(
                btn_name, 0) + 1
            print(f"Mouse {btn_name} button clicked at ({x}, {y})")

    # Start the listener if showing clicks
    listener = None
    if show_clicks:
        listener = Listener(on_click=on_click)
        listener.start()

    try:
        print("\nMonitoring mouse position. Press Ctrl+C to stop.")
        print("=" * 50)
        print(
            f"{'Time (s)':10} | {'X':6} | {'Y':6} | {'Left Clicks':12} | {'Right Clicks':12}")
        print("-" * 50)

        while True:
            current_time = time.time() - start_time
            x, y = mouse.position

            # Format and print the current position
            print(f"{current_time:10.2f} | {x:6} | {y:6} | {click_count.get('left', 0):12} | {click_count.get('right', 0):12}", end='\r')

            # Check if duration has elapsed
            if duration is not None and current_time >= duration:
                break

            time.sleep(update_interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
    finally:
        if listener:
            listener.stop()

        # Print summary
        end_time = time.time() - start_time
        print("\n" + "=" * 50)
        print(f"Monitoring session summary:")
        print(f"- Duration: {end_time:.2f} seconds")
        print(f"- Left clicks: {click_count.get('left', 0)}")
        print(f"- Right clicks: {click_count.get('right', 0)}")
        print("=" * 50)


def smooth_move(start_x, start_y, end_x, end_y, duration=1.0, steps=100):
    """
    Move the mouse smoothly from start position to end position.

    Args:
        start_x (int): Starting X coordinate
        start_y (int): Starting Y coordinate
        end_x (int): Ending X coordinate
        end_y (int): Ending Y coordinate
        duration (float): Total duration of the movement in seconds
        steps (int): Number of intermediate steps
    """
    mouse = Controller()

    # Calculate the distance to move
    dx = end_x - start_x
    dy = end_y - start_y

    # Calculate the time to sleep between steps
    sleep_time = duration / steps

    print(
        f"Moving mouse smoothly from ({start_x}, {start_y}) to ({end_x}, {end_y}) over {duration} seconds")

    # Use easing function for smoother acceleration/deceleration
    for step in range(steps + 1):
        # Use sine easing for smooth acceleration and deceleration
        t = step / steps
        # Ease in-out sine function
        ease = 0.5 - 0.5 * math.cos(math.pi * t)

        # Calculate intermediate position
        ix = start_x + dx * ease
        iy = start_y + dy * ease

        # Move to intermediate position
        mouse.position = (ix, iy)

        # Sleep for a short time
        time.sleep(sleep_time)

    # Ensure we end up exactly at the target position
    mouse.position = (end_x, end_y)
    print(
        f"Smooth movement complete. Current mouse position: {mouse.position}")


def perform_click(button='left', count=1, interval=0.1, double=False, delay_after=0):
    """
    Perform mouse clicks at the current position.

    Args:
        button (str): Which button to click ('left' or 'right')
        count (int): Number of clicks to perform
        interval (float): Time between clicks in seconds
        double (bool): Whether to perform double-clicks (overrides count)
        delay_after (float): Delay in seconds after all clicks are done
    """
    mouse = Controller()

    # Map string button name to pynput Button
    button_map = {
        'left': Button.left,
        'right': Button.right
    }

    if button not in button_map:
        print(f"Invalid button: {button}. Using left button instead.")
        button = 'left'

    mouse_button = button_map[button]

    if double:
        print(f"Performing double {button} click at {mouse.position}")
        mouse.click(mouse_button, 2)
    else:
        if count == 1:
            print(f"Performing {button} click at {mouse.position}")
            mouse.click(mouse_button)
        else:
            print(
                f"Performing {count} {button} clicks at {mouse.position} with {interval}s interval")
            for i in range(count):
                mouse.click(mouse_button)
                if i < count - 1:  # Don't sleep after the last click
                    time.sleep(interval)

    if delay_after > 0:
        print(f"Waiting for {delay_after} seconds after clicking...")
        time.sleep(delay_after)


def perform_drag(start_x, start_y, end_x, end_y, button='left', smooth=True, duration=1.0, steps=100, delay_after=0,
                 click_before=False, click_after=False, click_button=None, click_count=1, click_interval=0.1,
                 double_click=False, click_delay=0):
    """
    Perform a drag operation from start to end coordinates with optional clicks before or after.

    Args:
        start_x (int): Starting X coordinate
        start_y (int): Starting Y coordinate
        end_x (int): Ending X coordinate
        end_y (int): Ending Y coordinate
        button (str): Which button to use for dragging ('left' or 'right')
        smooth (bool): Whether to move smoothly during the drag
        duration (float): Duration of the drag in seconds
        steps (int): Number of steps for smooth movement
        delay_after (float): Delay in seconds after dragging
        click_before (bool): Whether to click before dragging
        click_after (bool): Whether to click after dragging
        click_button (str): Which button to use for clicking ('left' or 'right')
        click_count (int): Number of clicks to perform
        click_interval (float): Time between clicks in seconds
        double_click (bool): Whether to perform a double-click
        click_delay (float): Delay in seconds after clicking
    """
    mouse = Controller()

    # Map string button name to pynput Button
    button_map = {
        'left': Button.left,
        'right': Button.right
    }

    if button not in button_map:
        print(f"Invalid button: {button}. Using left button instead.")
        button = 'left'

    mouse_button = button_map[button]

    # Move to start position
    mouse.position = (start_x, start_y)
    print(f"Positioned at start coordinates: ({start_x}, {start_y})")

    # Perform click before dragging if requested
    if click_before:
        click_btn = click_button or button  # Use specified click button or drag button
        print(f"Performing click before drag...")
        perform_click(click_btn, click_count, click_interval,
                      double_click, click_delay)

    # Press and hold the button
    mouse.press(mouse_button)
    print(f"Pressed {button} button, starting drag operation")

    # Move to end position (smoothly or directly)
    if smooth:
        smooth_move(start_x, start_y, end_x, end_y, duration, steps)
    else:
        mouse.position = (end_x, end_y)
        print(f"Moved to end coordinates: ({end_x}, {end_y})")

    # Release the button
    mouse.release(mouse_button)
    print(f"Released {button} button, drag operation complete")

    # Perform click after dragging if requested
    if click_after:
        click_btn = click_button or button  # Use specified click button or drag button
        print(f"Performing click after drag...")
        perform_click(click_btn, click_count, click_interval,
                      double_click, click_delay)

    if delay_after > 0:
        print(f"Waiting for {delay_after} seconds after dragging...")
        time.sleep(delay_after)


def move_mouse(x, y, delay=0, check_bounds=True, smooth=False, smooth_duration=1.0, smooth_steps=100,
               click=None, click_count=1, click_interval=0.1, double_click=False, click_delay=0,
               drag_to_x=None, drag_to_y=None, drag_smooth=True,
               click_before_drag=False, click_after_drag=False):
    """
    Move the mouse to the specified coordinates and optionally click or drag.

    Args:
        x (int): X coordinate
        y (int): Y coordinate
        delay (float): Delay in seconds before moving the mouse
        check_bounds (bool): Whether to check if coordinates are within screen bounds
        smooth (bool): Whether to move the mouse smoothly to the target
        smooth_duration (float): Duration of smooth movement in seconds
        smooth_steps (int): Number of steps for smooth movement
        click (str): Which button to click after moving ('left', 'right', or None for no click)
        click_count (int): Number of clicks to perform
        click_interval (float): Time between clicks in seconds
        double_click (bool): Whether to perform a double-click
        click_delay (float): Delay in seconds after clicking
        drag_to_x (int): X coordinate to drag to (None for no drag)
        drag_to_y (int): Y coordinate to drag to (None for no drag)
        drag_smooth (bool): Whether to move smoothly during the drag
        click_before_drag (bool): Whether to click before dragging
        click_after_drag (bool): Whether to click after dragging
    """
    mouse = Controller()

    if check_bounds:
        screen_width, screen_height = get_screen_resolution()
        print(f"Detected screen resolution: {screen_width}x{screen_height}")

        # Check initial coordinates
        if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
            print(
                f"Warning: Coordinates ({x}, {y}) are outside screen bounds ({screen_width}x{screen_height})")
            print("Do you want to continue anyway? (y/n)")
            response = input().lower()
            if response != 'y' and response != 'yes':
                print("Operation cancelled.")
                return

        # Check drag coordinates if applicable
        if drag_to_x is not None and drag_to_y is not None:
            if drag_to_x < 0 or drag_to_x >= screen_width or drag_to_y < 0 or drag_to_y >= screen_height:
                print(
                    f"Warning: Drag coordinates ({drag_to_x}, {drag_to_y}) are outside screen bounds ({screen_width}x{screen_height})")
                print("Do you want to continue anyway? (y/n)")
                response = input().lower()
                if response != 'y' and response != 'yes':
                    print("Operation cancelled.")
                    return

    if delay > 0:
        print(f"Waiting for {delay} seconds before moving mouse...")
        time.sleep(delay)

    # Move to the initial position
    if smooth:
        # Get current mouse position as starting point
        current_pos = mouse.position
        smooth_move(current_pos[0], current_pos[1], x,
                    y, smooth_duration, smooth_steps)
    else:
        print(f"Moving mouse to coordinates: ({x}, {y})")
        mouse.position = (x, y)
        print(f"Current mouse position: {mouse.position}")

    # Perform drag if coordinates are provided
    if drag_to_x is not None and drag_to_y is not None:
        perform_drag(x, y, drag_to_x, drag_to_y,
                     button=click or 'left',  # Use click button or default to left
                     smooth=drag_smooth,
                     duration=smooth_duration,
                     steps=smooth_steps,
                     delay_after=click_delay,
                     click_before=click_before_drag,
                     click_after=click_after_drag,
                     click_button=click,
                     click_count=click_count,
                     click_interval=click_interval,
                     double_click=double_click,
                     click_delay=click_delay)
    # Otherwise perform click if requested
    elif click:
        perform_click(click, click_count, click_interval,
                      double_click, click_delay)


def main():
    """Parse command line arguments and move the mouse accordingly."""
    parser = argparse.ArgumentParser(
        description='Move the mouse to specified coordinates and optionally click or drag.')

    parser.add_argument('x', type=int, nargs='?',
                        help='X coordinate')
    parser.add_argument('y', type=int, nargs='?',
                        help='Y coordinate')

    # Movement options
    parser.add_argument('-d', '--delay', type=float, default=0,
                        help='Delay in seconds before moving the mouse (default: 0)')
    parser.add_argument('--ignore-bounds', action='store_true',
                        help='Ignore screen boundary checks')
    parser.add_argument('--smooth', action='store_true',
                        help='Move the mouse smoothly to the target coordinates')
    parser.add_argument('--duration', type=float, default=1.0,
                        help='Duration of smooth movement in seconds (default: 1.0)')
    parser.add_argument('--steps', type=int, default=100,
                        help='Number of steps for smooth movement (default: 100)')

    # Click options
    click_group = parser.add_argument_group('Click options')
    click_group.add_argument('--left-click', action='store_true',
                             help='Perform a left click after moving the mouse')
    click_group.add_argument('--right-click', action='store_true',
                             help='Perform a right click after moving the mouse')
    click_group.add_argument('--click-count', type=int, default=1,
                             help='Number of clicks to perform (default: 1)')
    click_group.add_argument('--click-interval', type=float, default=0.1,
                             help='Time between clicks in seconds (default: 0.1)')
    click_group.add_argument('--double', action='store_true',
                             help='Perform a double-click (overrides click-count)')
    click_group.add_argument('--click-delay', type=float, default=0,
                             help='Delay in seconds after clicking (default: 0)')

    # Drag options
    drag_group = parser.add_argument_group('Drag options')
    drag_group.add_argument('--drag-to-x', type=int,
                            help='X coordinate to drag to')
    drag_group.add_argument('--drag-to-y', type=int,
                            help='Y coordinate to drag to')
    drag_group.add_argument('--no-drag-smooth', action='store_true',
                            help='Disable smooth movement during drag')
    drag_group.add_argument('--click-before-drag', action='store_true',
                            help='Perform a click before starting the drag operation')
    drag_group.add_argument('--click-after-drag', action='store_true',
                            help='Perform a click after completing the drag operation')

    # Monitor options
    monitor_group = parser.add_argument_group('Monitor options')
    monitor_group.add_argument('--monitor', action='store_true',
                               help='Monitor and display mouse position in real-time')
    monitor_group.add_argument('--monitor-interval', type=float, default=0.1,
                               help='Update interval for monitor in seconds (default: 0.1)')
    monitor_group.add_argument('--monitor-duration', type=float,
                               help='Duration to monitor in seconds (default: indefinite)')
    monitor_group.add_argument('--no-monitor-clicks', action='store_true',
                               help='Disable click detection in monitor mode')

    # Show resolution
    parser.add_argument('--show-resolution', action='store_true',
                        help='Show screen resolution and exit')

    args = parser.parse_args()

    # Show resolution and exit if requested
    if args.show_resolution:
        width, height = get_screen_resolution()
        print(f"Screen resolution: {width}x{height}")
        return

    # Monitor mode
    if args.monitor:
        monitor_mouse_position(
            update_interval=args.monitor_interval,
            show_clicks=not args.no_monitor_clicks,
            duration=args.monitor_duration
        )
        return

    # If no coordinates are provided and not in monitor mode, show help
    if args.x is None or args.y is None:
        parser.error(
            "the following arguments are required: x, y (unless --show-resolution or --monitor is specified)")

    # Determine which click to perform (if any)
    click = None
    if args.left_click:
        click = 'left'
    elif args.right_click:
        click = 'right'

    # Check if drag coordinates are provided
    drag_to_x = args.drag_to_x
    drag_to_y = args.drag_to_y

    # Both drag coordinates must be provided or none
    if (drag_to_x is None) != (drag_to_y is None):
        parser.error(
            "Both --drag-to-x and --drag-to-y must be provided for drag operation")

    # Move the mouse (and click/drag if requested)
    move_mouse(
        args.x,
        args.y,
        args.delay,
        not args.ignore_bounds,
        args.smooth,
        args.duration,
        args.steps,
        click,
        args.click_count,
        args.click_interval,
        args.double,
        args.click_delay,
        drag_to_x,
        drag_to_y,
        not args.no_drag_smooth,
        args.click_before_drag,
        args.click_after_drag
    )


if __name__ == "__main__":
    main()
