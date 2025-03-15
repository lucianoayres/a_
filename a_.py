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
from pynput.mouse import Controller as MouseController, Button, Listener
from pynput.keyboard import Controller as KeyboardController, Key, KeyCode
import subprocess
import re
import platform
import json
import os
import shlex


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
    mouse = MouseController()
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
    mouse = MouseController()
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
    mouse = MouseController()

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
    mouse = MouseController()

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
    mouse = MouseController()

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
    mouse = MouseController()

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


def perform_key_press(key, modifiers=None, count=1, interval=0.1, delay_after=0):
    """
    Perform keyboard key press with optional modifiers.

    Args:
        key (str): The key to press (e.g., 'a', 'enter', 'space', etc.)
        modifiers (list): List of modifiers to hold while pressing the key (e.g., ['ctrl', 'shift'])
        count (int): Number of key presses to perform
        interval (float): Time between key presses in seconds
        delay_after (float): Delay in seconds after all key presses are done
    """
    keyboard = KeyboardController()

    # Map string key names to pynput Key constants
    special_key_map = {
        'enter': Key.enter,
        'esc': Key.esc,
        'escape': Key.esc,
        'space': Key.space,
        'tab': Key.tab,
        'backspace': Key.backspace,
        'delete': Key.delete,
        'up': Key.up,
        'down': Key.down,
        'left': Key.left,
        'right': Key.right,
        'home': Key.home,
        'end': Key.end,
        'page_up': Key.page_up,
        'page_down': Key.page_down,
        'f1': Key.f1,
        'f2': Key.f2,
        'f3': Key.f3,
        'f4': Key.f4,
        'f5': Key.f5,
        'f6': Key.f6,
        'f7': Key.f7,
        'f8': Key.f8,
        'f9': Key.f9,
        'f10': Key.f10,
        'f11': Key.f11,
        'f12': Key.f12,
    }

    # Map modifier names to pynput Key constants
    modifier_key_map = {
        'ctrl': Key.ctrl,
        'control': Key.ctrl,
        'alt': Key.alt,
        'shift': Key.shift,
        'cmd': Key.cmd,
        'command': Key.cmd,
        'win': Key.cmd,
        'windows': Key.cmd,
    }

    # Convert key string to pynput key
    pynput_key = None
    if key.lower() in special_key_map:
        pynput_key = special_key_map[key.lower()]
    elif len(key) == 1:
        pynput_key = key
    else:
        print(f"Warning: Unrecognized key '{key}'. Using as literal text.")
        pynput_key = key

    # Convert modifiers to pynput keys
    pynput_modifiers = []
    if modifiers:
        for mod in modifiers:
            if mod.lower() in modifier_key_map:
                pynput_modifiers.append(modifier_key_map[mod.lower()])
            else:
                print(f"Warning: Unrecognized modifier '{mod}'. Ignoring.")

    # Print information about the key press
    mod_str = " + ".join(modifiers) if modifiers else "no modifiers"
    print(f"Performing {count} key press(es) of '{key}' with {mod_str}")

    # Perform the key press(es)
    for i in range(count):
        # Press and hold modifiers
        for mod in pynput_modifiers:
            keyboard.press(mod)

        try:
            # Press and release the main key
            keyboard.press(pynput_key)
            keyboard.release(pynput_key)
        finally:
            # Release modifiers (ensure they're released even if an error occurs)
            for mod in reversed(pynput_modifiers):
                keyboard.release(mod)

        # Wait between key presses
        if i < count - 1:  # Don't sleep after the last press
            time.sleep(interval)

    # Wait after key presses if requested
    if delay_after > 0:
        print(f"Waiting for {delay_after} seconds after key press...")
        time.sleep(delay_after)


def perform_type(text, interval=0.05, delay_after=0):
    """
    Type a sequence of text characters.

    Args:
        text (str): The text to type
        interval (float): Time between key presses in seconds
        delay_after (float): Delay in seconds after typing is done
    """
    keyboard = KeyboardController()

    print(f"Typing text: '{text}'")

    # Type each character with the specified interval
    for char in text:
        keyboard.press(char)
        keyboard.release(char)
        time.sleep(interval)

    # Wait after typing if requested
    if delay_after > 0:
        print(f"Waiting for {delay_after} seconds after typing...")
        time.sleep(delay_after)


def perform_sequence(actions):
    """
    Perform a sequence of actions.

    Args:
        actions (list): List of action dictionaries, each containing the action type and parameters
    """
    for i, action in enumerate(actions):
        print(f"Performing action {i+1}/{len(actions)}: {action['type']}")

        if action['type'] == 'move':
            move_mouse(
                action['x'],
                action['y'],
                action.get('delay', 0),
                action.get('check_bounds', True),
                action.get('smooth', False),
                action.get('smooth_duration', 1.0),
                action.get('smooth_steps', 100),
                action.get('click'),
                action.get('click_count', 1),
                action.get('click_interval', 0.1),
                action.get('double_click', False),
                action.get('click_delay', 0),
                action.get('drag_to_x'),
                action.get('drag_to_y'),
                action.get('drag_smooth', True),
                action.get('click_before_drag', False),
                action.get('click_after_drag', False)
            )
        elif action['type'] == 'key':
            perform_key_press(
                action['key'],
                action.get('modifiers'),
                action.get('count', 1),
                action.get('interval', 0.1),
                action.get('delay_after', 0)
            )
        elif action['type'] == 'click':
            perform_click(
                action.get('button', 'left'),
                action.get('count', 1),
                action.get('interval', 0.1),
                action.get('double', False),
                action.get('delay_after', 0)
            )
        elif action['type'] == 'wait':
            delay = action.get('seconds', 1.0)
            print(f"Waiting for {delay} seconds...")
            time.sleep(delay)
        elif action['type'] == 'type':
            perform_type(
                action['text'],
                action.get('interval', 0.05),
                action.get('delay_after', 0)
            )
        else:
            print(
                f"Warning: Unknown action type '{action['type']}'. Skipping.")

        # Wait between actions if specified
        if i < len(actions) - 1 and action.get('delay_after_action', 0) > 0:
            delay = action.get('delay_after_action')
            print(f"Waiting {delay} seconds before next action...")
            time.sleep(delay)


def parse_action_sequence(sequence_str):
    """
    Parse a sequence string into a list of action dictionaries.

    Format: "action1; action2; action3"
    Where each action can be:
    - "move X Y" - Move to coordinates X,Y
    - "click [left|right] [count]" - Click with specified button and count
    - "key KEY [modifiers...]" - Press a key with optional modifiers
    - "wait SECONDS" - Wait for specified seconds
    - "drag X Y" - Drag from current position to X,Y
    - "drag_from X1 Y1 X2 Y2" - Drag from X1,Y1 to X2,Y2
    - "type TEXT" - Type a sequence of text

    Args:
        sequence_str (str): String containing sequence of actions

    Returns:
        list: List of action dictionaries
    """
    actions = []

    # Split the sequence by semicolons
    action_strings = sequence_str.split(';')

    for action_str in action_strings:
        action_str = action_str.strip()
        if not action_str:
            continue

        # Split the action into parts, preserving quoted strings
        parts = shlex.split(action_str)
        action_type = parts[0].lower()

        if action_type == 'move' and len(parts) >= 3:
            try:
                x = int(parts[1])
                y = int(parts[2])
                action = {
                    'type': 'move',
                    'x': x,
                    'y': y,
                    'smooth': '--smooth' in parts,
                }
                actions.append(action)
            except ValueError:
                print(
                    f"Warning: Invalid coordinates in '{action_str}'. Skipping.")

        elif action_type == 'click' and len(parts) >= 2:
            button = parts[1].lower() if len(parts) >= 2 else 'left'
            if button not in ['left', 'right']:
                button = 'left'

            count = 1
            if len(parts) >= 3:
                try:
                    count = int(parts[2])
                except ValueError:
                    pass

            action = {
                'type': 'click',
                'button': button,
                'count': count,
                'double': '--double' in parts
            }
            actions.append(action)

        elif action_type == 'key' and len(parts) >= 2:
            key = parts[1]
            modifiers = [mod for mod in parts[2:] if not mod.startswith('--')]

            action = {
                'type': 'key',
                'key': key,
                'modifiers': modifiers if modifiers else None
            }
            actions.append(action)

        elif action_type == 'wait' and len(parts) >= 2:
            try:
                seconds = float(parts[1])
                action = {
                    'type': 'wait',
                    'seconds': seconds
                }
                actions.append(action)
            except ValueError:
                print(
                    f"Warning: Invalid wait time in '{action_str}'. Skipping.")

        elif action_type == 'drag' and len(parts) >= 3:
            try:
                # Drag from current position to specified coordinates
                x = int(parts[1])
                y = int(parts[2])

                # Create a move action with drag parameters
                action = {
                    'type': 'move',
                    'x': actions[-1]['x'] if actions and actions[-1]['type'] == 'move' else None,
                    'y': actions[-1]['y'] if actions and actions[-1]['type'] == 'move' else None,
                    'drag_to_x': x,
                    'drag_to_y': y,
                    'drag_smooth': not '--no-smooth' in parts,
                    'click_before_drag': '--click-before' in parts,
                    'click_after_drag': '--click-after' in parts
                }

                # If we don't have a previous move action, we need to get current mouse position
                if action['x'] is None or action['y'] is None:
                    print(
                        "Warning: 'drag' should be preceded by a 'move' action. Using current mouse position.")
                    mouse = MouseController()
                    pos = mouse.position
                    action['x'] = pos[0]
                    action['y'] = pos[1]

                actions.append(action)
            except ValueError:
                print(
                    f"Warning: Invalid coordinates in '{action_str}'. Skipping.")

        elif action_type == 'drag_from' and len(parts) >= 5:
            try:
                # Drag from specified start coordinates to specified end coordinates
                start_x = int(parts[1])
                start_y = int(parts[2])
                end_x = int(parts[3])
                end_y = int(parts[4])

                # Create a move action with drag parameters
                action = {
                    'type': 'move',
                    'x': start_x,
                    'y': start_y,
                    'drag_to_x': end_x,
                    'drag_to_y': end_y,
                    'drag_smooth': not '--no-smooth' in parts,
                    'click_before_drag': '--click-before' in parts,
                    'click_after_drag': '--click-after' in parts
                }

                actions.append(action)
            except ValueError:
                print(
                    f"Warning: Invalid coordinates in '{action_str}'. Skipping.")

        elif action_type == 'type' and len(parts) >= 2:
            # Get the text to type (all parts after the command)
            text = parts[1]

            # Extract options
            interval = 0.05  # Default typing interval
            for i, part in enumerate(parts[2:]):
                if part.startswith('--interval='):
                    try:
                        interval = float(part.split('=')[1])
                    except (ValueError, IndexError):
                        print(
                            f"Warning: Invalid interval in '{part}'. Using default.")

            action = {
                'type': 'type',
                'text': text,
                'interval': interval
            }
            actions.append(action)

        else:
            print(f"Warning: Unrecognized action '{action_str}'. Skipping.")

    return actions


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

    # Keyboard options
    keyboard_group = parser.add_argument_group('Keyboard options')
    keyboard_group.add_argument('--key', type=str,
                                help='Key to press (e.g., a, enter, space, etc.)')
    keyboard_group.add_argument('--modifiers', type=str, nargs='+',
                                help='Modifiers to hold while pressing the key (e.g., ctrl shift)')
    keyboard_group.add_argument('--key-count', type=int, default=1,
                                help='Number of key presses to perform (default: 1)')
    keyboard_group.add_argument('--key-interval', type=float, default=0.1,
                                help='Time between key presses in seconds (default: 0.1)')
    keyboard_group.add_argument('--key-delay', type=float, default=0,
                                help='Delay in seconds after key press (default: 0)')
    keyboard_group.add_argument('--type', type=str,
                                help='Type a sequence of text')
    keyboard_group.add_argument('--type-interval', type=float, default=0.05,
                                help='Time between key presses when typing (default: 0.05)')
    keyboard_group.add_argument('--type-delay', type=float, default=0,
                                help='Delay in seconds after typing (default: 0)')

    # Sequence options
    sequence_group = parser.add_argument_group('Sequence options')
    sequence_group.add_argument('--sequence', type=str,
                                help='JSON string or file path defining a sequence of actions to perform')
    sequence_group.add_argument('--then-key', type=str,
                                help='Key to press after moving the mouse (shorthand for sequence)')
    sequence_group.add_argument('--then-wait', type=float,
                                help='Seconds to wait between mouse movement and key press (used with --then-key)')
    sequence_group.add_argument('--then-click', choices=['left', 'right'],
                                help='Perform a click after moving the mouse (shorthand for sequence)')
    sequence_group.add_argument('--click-before-key', choices=['left', 'right'],
                                help='Perform a click before pressing the key (used with --then-key)')
    sequence_group.add_argument('--do', type=str,
                                help='Perform a sequence of actions in a simple format: "move X Y; click left; key a"')

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

    # Keyboard mode (standalone)
    if args.key and not (args.x is not None and args.y is not None) and not args.sequence and not args.then_key:
        perform_key_press(
            args.key,
            args.modifiers,
            args.key_count,
            args.key_interval,
            args.key_delay
        )
        return

    # Type mode (standalone)
    if args.type and not (args.x is not None and args.y is not None) and not args.sequence:
        perform_type(
            args.type,
            args.type_interval,
            args.type_delay
        )
        return

    # Sequence mode
    if args.sequence:
        try:
            # Check if the sequence is a file path or a JSON string
            if args.sequence.endswith('.json') and os.path.isfile(args.sequence):
                with open(args.sequence, 'r') as f:
                    actions = json.load(f)
            else:
                actions = json.loads(args.sequence)

            # Validate that actions is a list
            if not isinstance(actions, list):
                parser.error("Sequence must be a list of action objects")

            perform_sequence(actions)
            return
        except json.JSONDecodeError:
            parser.error("Invalid JSON format for sequence")
        except FileNotFoundError:
            parser.error(f"Sequence file not found: {args.sequence}")
        except Exception as e:
            parser.error(f"Error processing sequence: {str(e)}")

    # Shorthand sequence: move then key
    if args.x is not None and args.y is not None and args.then_key:
        actions = [
            {
                'type': 'move',
                'x': args.x,
                'y': args.y,
                'delay': args.delay,
                'check_bounds': not args.ignore_bounds,
                'smooth': args.smooth,
                'smooth_duration': args.duration,
                'smooth_steps': args.steps
            }
        ]

        # Add click before key if specified
        if args.click_before_key:
            actions.append({
                'type': 'click',
                'button': args.click_before_key,
                'count': args.click_count,
                'interval': args.click_interval,
                'double': args.double
            })

        # Add wait if specified
        if args.then_wait:
            actions.append({
                'type': 'wait',
                'seconds': args.then_wait
            })

        # Add key press
        actions.append({
            'type': 'key',
            'key': args.then_key,
            'modifiers': args.modifiers,
            'count': args.key_count,
            'interval': args.key_interval,
            'delay_after': args.key_delay
        })

        perform_sequence(actions)
        return

    # Shorthand sequence: move then click
    if args.x is not None and args.y is not None and args.then_click:
        actions = [
            {
                'type': 'move',
                'x': args.x,
                'y': args.y,
                'delay': args.delay,
                'check_bounds': not args.ignore_bounds,
                'smooth': args.smooth,
                'smooth_duration': args.duration,
                'smooth_steps': args.steps
            },
            {
                'type': 'click',
                'button': args.then_click,
                'count': args.click_count,
                'interval': args.click_interval,
                'double': args.double,
                'delay_after': args.click_delay
            }
        ]

        # Add wait if specified
        if args.then_wait and len(actions) > 1:
            actions.insert(1, {
                'type': 'wait',
                'seconds': args.then_wait
            })

        perform_sequence(actions)
        return

    # Simple sequence mode
    if args.do:
        try:
            actions = parse_action_sequence(args.do)
            if actions:
                perform_sequence(actions)
            else:
                parser.error("No valid actions found in the sequence")
            return
        except Exception as e:
            parser.error(f"Error processing sequence: {str(e)}")

    # If no coordinates are provided and not in monitor, keyboard, or sequence mode, show help
    if args.x is None or args.y is None:
        parser.error(
            "the following arguments are required: x, y (unless --show-resolution, --monitor, --key, or --sequence is specified)")

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
