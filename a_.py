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
from pynput.mouse import Controller as MouseController, Button, Listener as MouseListener
from pynput.keyboard import Controller as KeyboardController, Key, KeyCode, Listener as KeyboardListener
import subprocess
import re
import platform
import json
import os
import shlex


def find_window_linux(title=None, process=None):
    """
    Find a window on Linux using wmctrl.

    Args:
        title (str): Window title to search for
        process (str): Process name to search for

    Returns:
        tuple: (window_id, window_title) or (None, None) if not found
    """
    try:
        # Check if wmctrl is installed
        subprocess.run(['which', 'wmctrl'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: wmctrl is not installed. Please install it using:")
        print("sudo apt-get install wmctrl")
        return None, None

    try:
        # Get list of windows
        output = subprocess.check_output(['wmctrl', '-l', '-p'], text=True)

        for line in output.split('\n'):
            if not line.strip():
                continue

            parts = line.split(None, 4)
            if len(parts) < 4:
                continue

            window_id, desktop, pid, *rest = parts
            window_title = rest[-1] if rest else ""

            # If process name is specified, check if it matches
            if process:
                try:
                    proc_name = subprocess.check_output(
                        ['ps', '-p', pid, '-o', 'comm='], text=True).strip()
                    if process.lower() not in proc_name.lower():
                        continue
                except subprocess.CalledProcessError:
                    continue

            # If title is specified, check if it matches
            if title:
                if title.lower() not in window_title.lower():
                    continue

            return window_id, window_title

    except subprocess.CalledProcessError as e:
        print(f"Error finding window: {e}")

    return None, None


def find_window_macos(title=None, process=None):
    """
    Find a window on macOS using osascript.

    Args:
        title (str): Window title to search for
        process (str): Process name to search for

    Returns:
        tuple: (window_id, window_title) or (None, None) if not found
    """
    try:
        if process:
            script = f'''
                tell application "System Events"
                    set frontApp to first application process whose name contains "{process}"
                    return {{name of frontApp, frontApp}}
                end tell
            '''
        elif title:
            script = f'''
                tell application "System Events"
                    set targetWindow to first window whose name contains "{title}"
                    set frontApp to first application process whose window 1 is targetWindow
                    return {{name of frontApp, frontApp}}
                end tell
            '''
        else:
            return None, None

        result = subprocess.check_output(
            ['osascript', '-e', script], text=True)
        if result:
            return "macos_window", result.strip()  # macOS doesn't use window IDs like X11

    except subprocess.CalledProcessError as e:
        print(f"Error finding window: {e}")

    return None, None


def find_window_windows(title=None, process=None):
    """
    Find a window on Windows using PowerShell.

    Args:
        title (str): Window title to search for
        process (str): Process name to search for

    Returns:
        tuple: (window_id, window_title) or (None, None) if not found
    """
    try:
        if process:
            script = f'''
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            public class Win32 {{
                [DllImport("user32.dll")]
                public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

                [DllImport("user32.dll")]
                public static extern bool SetForegroundWindow(IntPtr hWnd);
            }}
"@

            $process = Get-Process | Where-Object {{ $_.ProcessName -like "*{process}*" }} | Select-Object -First 1
            if ($process) {{
                $process.MainWindowTitle
            }}
            '''
        elif title:
            script = f'''
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            public class Win32 {{
                [DllImport("user32.dll")]
                public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

                [DllImport("user32.dll")]
                public static extern bool SetForegroundWindow(IntPtr hWnd);
            }}
"@

            $windows = Get-Process | Where-Object {{$_.MainWindowTitle}} | Where-Object {{$_.MainWindowTitle -like "*{title}*"}}
            if ($windows) {{
                $windows[0].MainWindowTitle
            }}
            '''
        else:
            return None, None

        result = subprocess.check_output(
            ['powershell', '-Command', script], text=True)
        if result:
            return "windows_window", result.strip()

    except subprocess.CalledProcessError as e:
        print(f"Error finding window: {e}")

    return None, None


def activate_window_linux(window_id):
    """Activate a window on Linux using wmctrl."""
    try:
        subprocess.run(['wmctrl', '-i', '-a', window_id], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error activating window: {e}")
        return False


def activate_window_macos(window_info):
    """Activate a window on macOS using osascript."""
    try:
        script = f'''
            tell application "{window_info}"
                activate
            end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error activating window: {e}")
        return False


def activate_window_windows(window_title):
    """Activate a window on Windows using PowerShell."""
    try:
        script = f'''
        Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class Win32 {{
            [DllImport("user32.dll")]
            public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

            [DllImport("user32.dll")]
            public static extern bool SetForegroundWindow(IntPtr hWnd);
        }}
"@

        $window = Get-Process | Where-Object {{$_.MainWindowTitle -eq "{window_title}"}} | Select-Object -First 1
        if ($window) {{
            $hwnd = $window.MainWindowHandle
            [Win32]::SetForegroundWindow($hwnd)
        }}
        '''
        subprocess.run(['powershell', '-Command', script], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error activating window: {e}")
        return False


def find_and_activate_window(title=None, process=None, wait=1, required=True, retry_count=3):
    """
    Find and activate a window across different platforms.

    Args:
        title (str): Window title to search for
        process (str): Process name to search for
        wait (float): Time to wait after activating window
        required (bool): Whether finding the window is required
        retry_count (int): Number of times to retry finding the window

    Returns:
        bool: True if window was found and activated, False otherwise
    """
    system = platform.system()

    for attempt in range(retry_count):
        if attempt > 0:
            print(
                f"Retrying window search (attempt {attempt + 1}/{retry_count})...")
            time.sleep(1)

        window_id = None
        window_title = None

        if system == "Linux":
            window_id, window_title = find_window_linux(title, process)
            if window_id:
                success = activate_window_linux(window_id)
        elif system == "Darwin":  # macOS
            window_id, window_title = find_window_macos(title, process)
            if window_id:
                success = activate_window_macos(window_title)
        elif system == "Windows":
            window_id, window_title = find_window_windows(title, process)
            if window_id:
                success = activate_window_windows(window_title)
        else:
            print(f"Unsupported operating system: {system}")
            return False

        if window_id:
            print(f"Found window: {window_title}")
            if wait > 0:
                print(f"Waiting {wait} seconds for window to be ready...")
                time.sleep(wait)
            return True

    if required:
        search_term = f"title '{title}'" if title else f"process '{process}'"
        print(f"Error: Could not find window with {search_term}")
        sys.exit(1)

    return False


def get_all_monitors():
    """
    Get information about all connected monitors.

    Returns:
        list: List of dictionaries containing monitor information
              Each dictionary has keys: 'index', 'x', 'y', 'width', 'height', 'primary'
    """
    monitors = []
    system = platform.system()

    if system == "Linux":
        try:
            # Use xrandr to get monitor information
            output = subprocess.check_output(
                ["xrandr", "--current"], text=True)

            # Parse the output to extract monitor information
            current_monitor = None
            monitor_index = 0

            for line in output.split('\n'):
                # Check for connected displays
                if " connected " in line:
                    monitor_name = line.split(' ')[0]
                    is_primary = "primary" in line

                    # Extract resolution and position if available in this line
                    position_match = re.search(
                        r'(\d+)x(\d+)\+(\d+)\+(\d+)', line)

                    if position_match:
                        width = int(position_match.group(1))
                        height = int(position_match.group(2))
                        x = int(position_match.group(3))
                        y = int(position_match.group(4))

                        monitors.append({
                            'index': monitor_index,
                            'name': monitor_name,
                            'x': x,
                            'y': y,
                            'width': width,
                            'height': height,
                            'primary': is_primary
                        })

                        monitor_index += 1
                    else:
                        current_monitor = {
                            'index': monitor_index,
                            'name': monitor_name,
                            'primary': is_primary
                        }

                # If we have a current monitor but no position yet, look for resolution line
                elif current_monitor and line.strip().startswith(current_monitor['name']):
                    position_match = re.search(
                        r'(\d+)x(\d+)\+(\d+)\+(\d+)', line)

                    if position_match:
                        width = int(position_match.group(1))
                        height = int(position_match.group(2))
                        x = int(position_match.group(3))
                        y = int(position_match.group(4))

                        current_monitor.update({
                            'x': x,
                            'y': y,
                            'width': width,
                            'height': height
                        })

                        monitors.append(current_monitor)
                        current_monitor = None
                        monitor_index += 1

                # If we're processing a monitor and find a resolution line
                elif current_monitor and "*current" in line:
                    res_match = re.search(r'(\d+)x(\d+)', line)
                    if res_match:
                        current_monitor['width'] = int(res_match.group(1))
                        current_monitor['height'] = int(res_match.group(2))
                        # Assume position 0,0 if not specified
                        current_monitor['x'] = current_monitor.get('x', 0)
                        current_monitor['y'] = current_monitor.get('y', 0)

                        monitors.append(current_monitor)
                        current_monitor = None
                        monitor_index += 1

        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error detecting monitors using xrandr: {e}")

    elif system == "Darwin":  # macOS
        try:
            # Use system_profiler to get display information
            output = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"], text=True)

            # Parse the output to extract monitor information
            monitor_index = 0
            current_monitor = None

            for line in output.split('\n'):
                if "Resolution:" in line:
                    res_match = re.search(r'Resolution: (\d+) x (\d+)', line)
                    if res_match and current_monitor:
                        current_monitor['width'] = int(res_match.group(1))
                        current_monitor['height'] = int(res_match.group(2))

                elif "Origin:" in line:
                    origin_match = re.search(r'Origin: \((\d+), (\d+)\)', line)
                    if origin_match and current_monitor:
                        current_monitor['x'] = int(origin_match.group(1))
                        current_monitor['y'] = int(origin_match.group(2))

                        # If we have all the information, add the monitor
                        if all(k in current_monitor for k in ['width', 'height', 'x', 'y']):
                            monitors.append(current_monitor)
                            monitor_index += 1
                            current_monitor = None

                elif "Display Type:" in line or "Display:" in line:
                    # Start a new monitor
                    if current_monitor:
                        # If we have a partial monitor, add default values
                        current_monitor.setdefault('x', 0)
                        current_monitor.setdefault('y', 0)
                        if 'width' in current_monitor and 'height' in current_monitor:
                            monitors.append(current_monitor)
                            monitor_index += 1

                    display_name = line.split(':')[1].strip(
                    ) if ':' in line else f"Display {monitor_index}"
                    current_monitor = {
                        'index': monitor_index,
                        'name': display_name,
                        'primary': monitor_index == 0  # Assume first display is primary
                    }

            # Add the last monitor if it exists
            if current_monitor and 'width' in current_monitor and 'height' in current_monitor:
                current_monitor.setdefault('x', 0)
                current_monitor.setdefault('y', 0)
                monitors.append(current_monitor)

        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error detecting monitors using system_profiler: {e}")

    elif system == "Windows":
        try:
            # Use PowerShell to get monitor information
            ps_command = """
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.Screen]::AllScreens | ForEach-Object {
                $bounds = $_.Bounds
                $isPrimary = $_.Primary
                "$($bounds.X),$($bounds.Y),$($bounds.Width),$($bounds.Height),$($isPrimary)"
            }
            """
            output = subprocess.check_output(
                ["powershell", "-Command", ps_command], text=True)

            for i, line in enumerate(output.strip().split('\n')):
                parts = line.strip().split(',')
                if len(parts) == 5:
                    x, y, width, height, is_primary = parts
                    monitors.append({
                        'index': i,
                        'name': f"Display {i+1}",
                        'x': int(x),
                        'y': int(y),
                        'width': int(width),
                        'height': int(height),
                        'primary': is_primary.lower() == 'true'
                    })

        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error detecting monitors using PowerShell: {e}")

    # If no monitors were detected, add a fallback monitor
    if not monitors:
        # Try to get at least one monitor using the old method
        width, height = get_screen_resolution()
        monitors.append({
            'index': 0,
            'name': 'Default Display',
            'x': 0,
            'y': 0,
            'width': width,
            'height': height,
            'primary': True
        })

    return monitors


def get_screen_resolution():
    """
    Get the screen resolution of the primary monitor.

    Returns:
        tuple: (width, height) of the primary monitor
    """
    # Try to get all monitors first
    monitors = get_all_monitors()

    # Find the primary monitor
    for monitor in monitors:
        if monitor.get('primary', False):
            return monitor['width'], monitor['height']

    # If no primary monitor found, use the first one
    if monitors:
        return monitors[0]['width'], monitors[0]['height']

    # Fallback methods if get_all_monitors failed
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


def get_monitor_by_index(index):
    """
    Get monitor information by index.

    Args:
        index (int): The index of the monitor to retrieve

    Returns:
        dict: Monitor information or None if not found
    """
    monitors = get_all_monitors()

    for monitor in monitors:
        if monitor['index'] == index:
            return monitor

    return None


def list_monitors():
    """
    Print information about all detected monitors.
    """
    monitors = get_all_monitors()

    print("\nDetected Monitors:")
    print("=" * 80)
    print(f"{'Index':<6} | {'Name':<20} | {'Resolution':<12} | {'Position':<12} | {'Primary':<7}")
    print("-" * 80)

    for monitor in monitors:
        resolution = f"{monitor['width']}x{monitor['height']}"
        position = f"+{monitor['x']},+{monitor['y']}"
        primary = "Yes" if monitor['primary'] else "No"
        print(f"{monitor['index']:<6} | {monitor['name'][:20]:<20} | {resolution:<12} | "
              f"{position:<12} | {primary:<7}")

    print("=" * 80)


def convert_to_global_coordinates(x, y, monitor_index=None):
    """
    Convert monitor-relative coordinates to global screen coordinates.

    Args:
        x (int): X coordinate relative to the monitor
        y (int): Y coordinate relative to the monitor
        monitor_index (int): Index of the monitor (None for primary)

    Returns:
        tuple: (global_x, global_y) coordinates
    """
    monitors = get_all_monitors()

    # If no monitor index specified, use primary
    if monitor_index is None:
        for monitor in monitors:
            if monitor.get('primary', False):
                return x + monitor['x'], y + monitor['y']

        # If no primary found, use first monitor
        if monitors:
            return x + monitors[0]['x'], y + monitors[0]['y']
        return x, y

    # Find the specified monitor
    for monitor in monitors:
        if monitor['index'] == monitor_index:
            return x + monitor['x'], y + monitor['y']

    # Monitor not found, return original coordinates
    print(
        f"Warning: Monitor with index {monitor_index} not found. Using coordinates as-is.")
    return x, y


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
        listener = MouseListener(on_click=on_click)
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
                action.get('click_after_drag', False),
                action.get('monitor_index')
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
        elif action['type'] == 'scroll':
            perform_scroll(
                action['amount'],
                action.get('steps', 10),
                action.get('interval', 0.01),
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


def record_events(output_file, duration=None):
    """
    Record mouse and keyboard events and save them to a JSON file.

    Args:
        output_file (str): Path to save the recorded events
        duration (float): How long to record in seconds (None for indefinite)
    """
    events = []
    start_time = time.time()
    mouse = MouseController()
    recording = True
    last_position = mouse.position
    event_count = 0

    def on_move(x, y):
        if not recording:
            return False
        nonlocal last_position, event_count
        current_time = time.time() - start_time
        # Only record if position changed significantly (avoid micro-movements)
        if abs(x - last_position[0]) > 2 or abs(y - last_position[1]) > 2:
            events.append({
                "type": "move",
                "x": x,
                "y": y,
                "time": current_time,
                "smooth": True
            })
            last_position = (x, y)
            event_count += 1
            print(
                f"\rRecorded events: {event_count} | Last event: Mouse moved to ({x}, {y})", end="")

    def on_click(x, y, button, pressed):
        if not recording:
            return False
        nonlocal event_count
        current_time = time.time() - start_time
        if pressed:
            btn_name = "left" if button == Button.left else "right"
            events.append({
                "type": "click",
                "button": btn_name,
                "time": current_time
            })
            event_count += 1
            print(
                f"\rRecorded events: {event_count} | Last event: {btn_name.capitalize()} click at ({x}, {y})", end="")

    def on_scroll(x, y, dx, dy):
        if not recording:
            return False
        nonlocal event_count
        current_time = time.time() - start_time
        amount = int(dy * 10)
        direction = "up" if amount > 0 else "down"
        events.append({
            "type": "scroll",
            "amount": amount,
            "time": current_time
        })
        event_count += 1
        print(
            f"\rRecorded events: {event_count} | Last event: Scrolled {direction}", end="")

    def on_press(key):
        if not recording:
            return False
        nonlocal event_count
        current_time = time.time() - start_time

        # Handle special case for recording stop key (Esc)
        try:
            if key == Key.esc:
                print("\nStopping recording...")
                return False  # Stop listener
        except AttributeError:
            pass

        # Convert key to string representation
        key_str = None
        if hasattr(key, 'char'):
            key_str = key.char
        elif hasattr(key, 'name'):
            key_str = key.name

        if key_str:
            events.append({
                "type": "key",
                "key": key_str,
                "time": current_time
            })
            event_count += 1
            print(
                f"\rRecorded events: {event_count} | Last event: Key press '{key_str}'", end="")

    # Start listeners
    print("\nRecording mouse and keyboard events. Press Esc to stop.")
    print("=" * 50)
    print("Events will be shown here as they are recorded...")
    print("-" * 50)

    with MouseListener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as mouse_listener, \
            KeyboardListener(on_press=on_press) as kb_listener:

        try:
            while recording:
                current_time = time.time() - start_time
                if duration is not None and current_time >= duration:
                    print("\nRecording duration reached.")
                    break
                time.sleep(0.01)  # Reduce CPU usage

                if not mouse_listener.running or not kb_listener.running:
                    break

        except KeyboardInterrupt:
            print("\nRecording interrupted by user.")
            recording = False

        finally:
            # Stop listeners
            mouse_listener.stop()
            kb_listener.stop()

            # Add timing information
            for i in range(1, len(events)):
                events[i]['delay'] = events[i]['time'] - events[i-1]['time']
            if events:
                events[0]['delay'] = 0

            # Remove absolute timestamps
            for event in events:
                del event['time']

            # Save to file
            with open(output_file, 'w') as f:
                json.dump(events, f, indent=2)

            print("\n" + "=" * 50)
            print("Recording summary:")
            print(f"- Total events recorded: {event_count}")
            print(f"- Events saved to: {output_file}")
            print("=" * 50)


def replay_events(input_file):
    """
    Replay recorded events from a JSON file.

    Args:
        input_file (str): Path to the JSON file containing recorded events
    """
    try:
        with open(input_file, 'r') as f:
            events = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {input_file}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON file: {input_file}")
        return

    print(f"\nReplaying {len(events)} events from: {input_file}")
    print("=" * 50)
    print("Press Ctrl+C to stop replay")

    try:
        for i, event in enumerate(events, 1):
            # Get the delay for this event (will be used as movement duration for mouse moves)
            delay = event.get('delay', 0)

            print(f"Event {i}/{len(events)}: {event['type']}")

            if event['type'] == 'move':
                move_mouse(
                    event['x'],
                    event['y'],
                    smooth=event.get('smooth', False),
                    # Use recorded delay as movement duration
                    smooth_duration=delay if delay > 0 else 0.1
                )
            elif event['type'] == 'click':
                # Wait the delay before clicking
                if delay > 0:
                    time.sleep(delay)
                perform_click(
                    button=event.get('button', 'left'),
                    count=event.get('count', 1)
                )
            elif event['type'] == 'scroll':
                # Wait the delay before scrolling
                if delay > 0:
                    time.sleep(delay)
                perform_scroll(
                    amount=event['amount']
                )
            elif event['type'] == 'key':
                # Wait the delay before key press
                if delay > 0:
                    time.sleep(delay)
                perform_key_press(
                    event['key']
                )

    except KeyboardInterrupt:
        print("\nReplay stopped by user.")

    print("\nReplay complete.")


def move_mouse(x, y, delay=0, check_bounds=True, smooth=False, smooth_duration=1.0, smooth_steps=100, click=None, click_count=1, click_interval=0.1, double_click=False, click_delay=0, drag_to_x=None, drag_to_y=None, drag_smooth=True, click_before_drag=False, click_after_drag=False, monitor_index=None):
    """
    Move the mouse to specified coordinates with various options.

    Args:
        x (int): X coordinate
        y (int): Y coordinate
        delay (float): Delay before moving in seconds
        check_bounds (bool): Whether to check screen boundaries
        smooth (bool): Whether to move smoothly
        smooth_duration (float): Duration of smooth movement in seconds
        smooth_steps (int): Number of steps in smooth movement
        click (str): Button to click after moving ('left', 'right', None)
        click_count (int): Number of clicks
        click_interval (float): Interval between clicks
        double_click (bool): Whether to perform a double-click
        click_delay (float): Delay after clicking
        drag_to_x (int): X coordinate to drag to
        drag_to_y (int): Y coordinate to drag to
        drag_smooth (bool): Whether to move smoothly during drag
        click_before_drag (bool): Whether to click before dragging
        click_after_drag (bool): Whether to click after dragging
        monitor_index (int): Index of monitor to use for coordinates
    """
    mouse = MouseController()

    if delay > 0:
        time.sleep(delay)

    # Convert coordinates if monitor specified
    if monitor_index is not None:
        x, y = convert_to_global_coordinates(x, y, monitor_index)

    # Get current position for smooth movement
    start_x, start_y = mouse.position

    # Move the mouse
    if smooth:
        smooth_move(start_x, start_y, x, y, smooth_duration, smooth_steps)
    else:
        mouse.position = (x, y)

    # Handle clicking
    if click or double_click:
        perform_click(click, click_count, click_interval,
                      double_click, click_delay)

    # Handle dragging
    if drag_to_x is not None and drag_to_y is not None:
        if click_before_drag:
            perform_click(click or 'left')

        if drag_smooth:
            smooth_move(x, y, drag_to_x, drag_to_y)
        else:
            mouse.position = (drag_to_x, drag_to_y)

        if click_after_drag:
            perform_click(click or 'left')


def perform_click(button='left', count=1, interval=0.1, double=False, delay_after=0):
    """
    Perform mouse clicks.

    Args:
        button (str): Button to click ('left' or 'right')
        count (int): Number of clicks
        interval (float): Interval between clicks
        double (bool): Whether to perform a double-click
        delay_after (float): Delay after clicking
    """
    mouse = MouseController()
    btn = Button.left if button == 'left' else Button.right

    if double:
        count = 2
        interval = 0.1  # Standard double-click interval

    for _ in range(count):
        mouse.press(btn)
        mouse.release(btn)
        if _ < count - 1:  # Don't sleep after last click
            time.sleep(interval)

    if delay_after > 0:
        time.sleep(delay_after)


def perform_scroll(amount, steps=10, interval=0.01, delay_after=0):
    """
    Perform mouse scroll.

    Args:
        amount (int): Amount to scroll (positive for up, negative for down)
        steps (int): Number of steps to divide the scroll into
        interval (float): Interval between scroll steps
        delay_after (float): Delay after scrolling
    """
    mouse = MouseController()
    step_amount = amount / steps

    for _ in range(steps):
        mouse.scroll(0, step_amount)
        time.sleep(interval)

    if delay_after > 0:
        time.sleep(delay_after)


def perform_key_press(key, modifiers=None, count=1, interval=0.1, delay_after=0):
    """
    Perform keyboard key press.

    Args:
        key (str): Key to press
        modifiers (list): List of modifier keys to hold
        count (int): Number of times to press the key
        interval (float): Interval between key presses
        delay_after (float): Delay after key press
    """
    keyboard = KeyboardController()

    # Convert string key to Key object if it's a special key
    if hasattr(Key, key):
        key = getattr(Key, key)
    elif len(key) == 1:
        key = key
    else:
        print(f"Warning: Unknown key '{key}'")
        return

    # Handle modifiers
    active_modifiers = []
    if modifiers:
        for mod in modifiers:
            if hasattr(Key, mod.lower()):
                mod_key = getattr(Key, mod.lower())
                keyboard.press(mod_key)
                active_modifiers.append(mod_key)

    # Press the key the specified number of times
    for _ in range(count):
        keyboard.press(key)
        keyboard.release(key)
        if _ < count - 1:  # Don't sleep after last press
            time.sleep(interval)

    # Release modifiers
    for mod_key in active_modifiers:
        keyboard.release(mod_key)

    if delay_after > 0:
        time.sleep(delay_after)


def perform_type(text, interval=0.05, delay_after=0):
    """
    Type a sequence of text.

    Args:
        text (str): Text to type
        interval (float): Interval between keystrokes
        delay_after (float): Delay after typing
    """
    keyboard = KeyboardController()

    for char in text:
        keyboard.press(char)
        keyboard.release(char)
        time.sleep(interval)

    if delay_after > 0:
        time.sleep(delay_after)


def main():
    """Parse command line arguments and execute the appropriate action."""
    parser = argparse.ArgumentParser(
        description='Move the mouse to specified coordinates and perform mouse actions.')

    # Record and Replay options
    record_group = parser.add_argument_group('Record and Replay options')
    record_group.add_argument('--record', nargs='?', const='recorded_actions.json', metavar='OUTPUT_FILE',
                              help='Record mouse and keyboard events to a file (default: recorded_actions.json)')
    record_group.add_argument('--record-duration', type=float,
                              help='Duration to record in seconds (default: indefinite)')
    record_group.add_argument('--replay', nargs='?', const='recorded_actions.json', metavar='INPUT_FILE',
                              help='Replay recorded events from a file (default: recorded_actions.json)')

    # ... rest of the argument parsing ...

    args = parser.parse_args()

    # Handle record mode
    if args.record is not None:
        record_events(args.record, args.record_duration)
        return

    # Handle replay mode
    if args.replay is not None:
        replay_events(args.replay)
        return

    # ... rest of the main function ...


if __name__ == "__main__":
    main()
