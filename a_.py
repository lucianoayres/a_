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
    distance = math.sqrt(dx * dx + dy * dy)

    # Adjust steps based on distance (more steps for longer distances)
    steps = min(max(int(distance / 5), 50), 150)  # Between 50 and 150 steps

    # Calculate the time to sleep between steps
    sleep_time = duration / steps

    print(
        f"Moving mouse smoothly from ({start_x}, {start_y}) to ({end_x}, {end_y}) over {duration} seconds")

    def ease_in_out_quad(t):
        """Quadratic easing function for smooth acceleration and deceleration"""
        if t < 0.5:
            return 2 * t * t
        t = 2 * t - 2
        return -0.5 * (t * t - 2)

    # Move in steps using quadratic easing
    for step in range(steps + 1):
        t = step / steps
        # Apply easing
        ease = ease_in_out_quad(t)

        # Calculate intermediate position
        ix = start_x + dx * ease
        iy = start_y + dy * ease

        # Move to intermediate position
        mouse.position = (int(ix), int(iy))

        # Sleep for a fixed time between steps
        time.sleep(sleep_time)

    # Ensure we end up exactly at the target position
    mouse.position = (end_x, end_y)


def perform_sequence(actions):
    """
    Perform a sequence of actions.

    Args:
        actions (list): List of action dictionaries, each containing the action type and parameters
    """
    held_keys = {}  # Keep track of held keys

    for i, action in enumerate(actions):
        print(f"Performing action {i+1}/{len(actions)}: {action['type']}")

        # Validate action parameters
        try:
            validate_sequence_action(action)
        except ValueError as e:
            print(f"Error in action {i+1}: {e}")
            continue

        if action['type'] == 'window':
            # Handle window selection
            window_found = find_and_activate_window(
                title=action.get('title'),
                process=action.get('process'),
                wait=action.get('wait', 1.0),
                required=not action.get('not_required', False),
                retry_count=action.get('retry_count', 3)
            )
            if not window_found and not action.get('not_required', False):
                print("Stopping sequence due to window not found")
                break

        elif action['type'] == 'hold_key':
            key = action.get('key')
            if key:
                held_keys[key] = hold_key(key)
                print(f"Holding {key} key...")

        elif action['type'] == 'release_key':
            key = action.get('key')
            if key and key in held_keys:
                release_key(held_keys[key])
                del held_keys[key]
                print(f"Released {key} key")
            elif action.get('all', False):
                # Release all held keys
                for k, obj in held_keys.items():
                    release_key(obj)
                    print(f"Released {k} key")
                held_keys.clear()

        elif action['type'] == 'move':
            move_mouse(
                action['x'],
                action['y'],
                delay=action.get('delay', 0),
                check_bounds=action.get('check_bounds', True),
                smooth=action.get('smooth', False),
                smooth_duration=action.get('smooth_duration', 1.0),
                smooth_steps=action.get('smooth_steps', 100),
                click=action.get('click'),
                click_count=action.get('click_count', 1),
                click_interval=action.get('click_interval', 0.1),
                double_click=action.get('double_click', False),
                click_delay=action.get('click_delay', 0),
                drag_to_x=action.get('drag_to_x'),
                drag_to_y=action.get('drag_to_y'),
                drag_smooth=action.get('drag_smooth', True),
                click_before_drag=action.get('click_before_drag', False),
                click_after_drag=action.get('click_after_drag', False),
                monitor_index=action.get('monitor_index')
            )

        elif action['type'] == 'click':
            perform_click(
                button=action.get('button', 'left'),
                count=action.get('count', 1),
                interval=action.get('interval', 0.1),
                double=action.get('double', False),
                delay_after=action.get('delay_after', 0)
            )

        elif action['type'] == 'scroll':
            perform_scroll(
                amount=action['amount'],
                steps=action.get('steps', 10),
                interval=action.get('interval', 0.01),
                delay_after=action.get('delay_after', 0)
            )

        elif action['type'] == 'key':
            perform_key_press(
                action['key'],
                modifiers=action.get('modifiers'),
                count=action.get('count', 1),
                interval=action.get('interval', 0.1),
                delay_after=action.get('delay_after', 0)
            )

        elif action['type'] == 'type':
            perform_type(
                action['text'],
                interval=action.get('interval', 0.05),
                delay_after=action.get('delay_after', 0)
            )

        elif action['type'] == 'wait':
            delay = action.get('seconds', 1.0)
            print(f"Waiting {delay} seconds...")
            time.sleep(delay)

        # Wait between actions if specified
        if i < len(actions) - 1 and action.get('delay_after_action', 0) > 0:
            delay = action.get('delay_after_action')
            print(f"Waiting {delay} seconds before next action...")
            time.sleep(delay)

    # Release any remaining held keys
    for k, obj in held_keys.items():
        release_key(obj)
        print(f"Released {k} key")


def validate_sequence_action(action):
    """Validate a sequence action has all required parameters."""
    required_params = {
        'move': ['x', 'y'],
        'click': [],  # click has no required params, all have defaults
        'key': ['key'],
        'type': ['text'],
        'scroll': ['amount'],
        # at least one of these must be present
        'window': ['title', 'process'],
        'wait': ['seconds']
    }

    if action['type'] not in required_params:
        raise ValueError(f"Unknown action type: {action['type']}")

    if action['type'] == 'window':
        # Special case: window requires at least one of title or process
        if not action.get('title') and not action.get('process'):
            raise ValueError(
                "Window action requires either 'title' or 'process'")
        return

    missing = [p for p in required_params[action['type']]
               if p not in action]
    if missing:
        raise ValueError(
            f"Missing required parameters for {action['type']}: {missing}")


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
    held_keys = set()  # Track currently held keys
    last_window_check = 0
    WINDOW_CHECK_INTERVAL = 0.1  # Only check window every 100ms
    last_window = None
    MOVEMENT_THRESHOLD = 10  # Minimum pixel distance for recording movement
    MIN_MOVEMENT_DELAY = 0.05  # Minimum delay between recorded movements

    def get_active_window():
        """Get current active window information."""
        system = platform.system()
        if system == "Linux":
            try:
                output = subprocess.check_output(
                    ['xdotool', 'getactivewindow', 'getwindowname'], text=True).strip()
                return {'title': output}
            except (subprocess.SubprocessError, FileNotFoundError):
                return None
        elif system == "Darwin":
            try:
                script = '''
                    tell application "System Events"
                        set frontApp to first application process whose frontmost is true
                        return {name of frontApp, name of window 1 of frontApp}
                    end tell
                '''
                output = subprocess.check_output(
                    ['osascript', '-e', script], text=True).strip()
                app_name, window_title = output.split(', ')
                return {'process': app_name, 'title': window_title}
            except (subprocess.SubprocessError, FileNotFoundError):
                return None
        elif system == "Windows":
            try:
                script = '''
                Add-Type @"
                    using System;
                    using System.Runtime.InteropServices;
                    public class Win32 {
                        [DllImport("user32.dll")]
                        public static extern IntPtr GetForegroundWindow();
                        
                        [DllImport("user32.dll")]
                        public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
                        
                        [DllImport("user32.dll")]
                        public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
                    }
"@

                $hwnd = [Win32]::GetForegroundWindow()
                $processId = 0
                [Win32]::GetWindowThreadProcessId($hwnd, [ref]$processId)
                $process = Get-Process -Id $processId
                $sb = New-Object System.Text.StringBuilder(256)
                [Win32]::GetWindowText($hwnd, $sb, 256)
                $windowTitle = $sb.ToString()
                Write-Output "$($process.ProcessName)|$windowTitle"
                '''
                output = subprocess.check_output(
                    ['powershell', '-Command', script], text=True).strip()
                process_name, window_title = output.split('|')
                return {'process': process_name, 'title': window_title}
            except (subprocess.SubprocessError, FileNotFoundError):
                return None
        return None

    def check_and_record_window_change():
        """Check if active window has changed and record if it has."""
        nonlocal event_count, last_window_check, last_window
        current_time = time.time()

        # Only check window periodically or during significant events
        if current_time - last_window_check < WINDOW_CHECK_INTERVAL:
            return

        last_window_check = current_time
        current_window = get_active_window()

        if current_window and (last_window is None or
                               any(current_window[k] != last_window[k] for k in current_window)):
            last_window = current_window
            events.append({
                "type": "window",
                "time": current_time - start_time,
                **current_window
            })
            event_count += 1
            print(
                f"\rRecorded events: {event_count} | Last event: Window changed to {current_window.get('title', '')}", end="")

    # Get initial window
    last_window = get_active_window()
    if last_window:
        events.append({
            "type": "window",
            "time": 0,
            **last_window
        })

    def on_move(x, y):
        if not recording:
            return False
        nonlocal last_position, event_count
        current_time = time.time() - start_time

        # Calculate distance moved
        dx = x - last_position[0]
        dy = y - last_position[1]
        distance = math.sqrt(dx*dx + dy*dy)

        # Only record if position changed significantly and enough time has passed
        if distance > MOVEMENT_THRESHOLD and (not events or
                                              events[-1]['type'] != 'move' or
                                              current_time - events[-1]['time'] >= MIN_MOVEMENT_DELAY):

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
            check_and_record_window_change()  # Check window on clicks
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
        check_and_record_window_change()  # Check window on scroll
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

    def get_key_name(key):
        """Convert key to a consistent string representation."""
        if isinstance(key, KeyCode):
            return key.char if key.char else f'<{key.vk}>'
        if isinstance(key, Key):
            name = key.name.lower()
            if name in ['ctrl_l', 'ctrl_r']:
                return 'ctrl'
            if name in ['alt_l', 'alt_r']:
                return 'alt'
            if name in ['shift_l', 'shift_r']:
                return 'shift'
            if name in ['cmd_l', 'cmd_r', 'cmd']:
                return 'cmd'
            return name
        return str(key)

    def is_modifier_key(key):
        """Check if the key is a modifier key."""
        if isinstance(key, Key):
            name = key.name.lower()
            return name in ['ctrl_l', 'ctrl_r', 'alt_l', 'alt_r', 'shift_l', 'shift_r', 'cmd_l', 'cmd_r', 'cmd']
        return False

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

        check_and_record_window_change()  # Check window on key press
        key_name = get_key_name(key)

        if is_modifier_key(key):
            # Record modifier key press as hold_key event
            if key_name not in held_keys:
                held_keys.add(key_name)
                events.append({
                    "type": "hold_key",
                    "key": key_name,
                    "time": current_time
                })
                event_count += 1
                print(
                    f"\rRecorded events: {event_count} | Last event: Hold key '{key_name}'", end="")
        else:
            # Regular key press
            events.append({
                "type": "key",
                "key": key_name,
                "time": current_time
            })
            event_count += 1
            print(
                f"\rRecorded events: {event_count} | Last event: Key press '{key_name}'", end="")

    def on_release(key):
        if not recording:
            return False
        nonlocal event_count
        current_time = time.time() - start_time

        check_and_record_window_change()  # Check window on key release
        key_name = get_key_name(key)

        if is_modifier_key(key) and key_name in held_keys:
            # Record modifier key release
            held_keys.remove(key_name)
            events.append({
                "type": "release_key",
                "key": key_name,
                "time": current_time
            })
            event_count += 1
            print(
                f"\rRecorded events: {event_count} | Last event: Release key '{key_name}'", end="")

    # Start listeners
    print("\nRecording mouse and keyboard events. Press Esc to stop.")
    print("=" * 50)
    print("Events will be shown here as they are recorded...")
    print("-" * 50)

    with MouseListener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as mouse_listener, \
            KeyboardListener(on_press=on_press, on_release=on_release) as kb_listener:

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

    # Keep track of held keys
    held_keys = {}
    current_window = None

    # Optimize delays for smoother playback
    MAX_MOVEMENT_DELAY = 0.05  # Cap movement delays
    CLICK_DELAY_FACTOR = 0.5   # Reduce click delays
    KEY_DELAY_FACTOR = 0.75    # Reduce key press delays

    try:
        for i, event in enumerate(events, 1):
            # Get and adjust the delay based on event type
            delay = event.get('delay', 0)

            if event['type'] == 'move':
                delay = min(delay, MAX_MOVEMENT_DELAY)
            elif event['type'] == 'click':
                delay *= CLICK_DELAY_FACTOR
            elif event['type'] == 'key':
                delay *= KEY_DELAY_FACTOR

            # Wait the adjusted delay before any action
            if delay > 0:
                time.sleep(delay)

            print(f"Event {i}/{len(events)}: {event['type']}")

            if event['type'] == 'window':
                # Try to find and activate the window
                window_found = False
                if 'process' in event:
                    print(f"Activating window for process: {event['process']}")
                    window_found = find_and_activate_window(
                        process=event['process'], wait=1, required=False)
                if not window_found and 'title' in event:
                    print(f"Activating window with title: {event['title']}")
                    window_found = find_and_activate_window(
                        title=event['title'], wait=1, required=False)
                if window_found:
                    current_window = event
                    print(
                        f"Successfully activated window: {event.get('title', event.get('process', 'Unknown'))}")
                else:
                    print(
                        f"Warning: Could not find window: {event.get('title', event.get('process', 'Unknown'))}")

            elif event['type'] == 'hold_key':
                key = event.get('key')
                if key:
                    held_keys[key] = hold_key(key)
                    print(f"Holding {key} key...")

            elif event['type'] == 'release_key':
                key = event.get('key')
                if key and key in held_keys:
                    release_key(held_keys[key])
                    del held_keys[key]
                    print(f"Released {key} key")

            elif event['type'] == 'move':
                move_mouse(
                    event['x'],
                    event['y'],
                    smooth=event.get('smooth', False),
                    smooth_duration=0.001  # Faster smooth movement
                )
            elif event['type'] == 'click':
                perform_click(
                    button=event.get('button', 'left'),
                    count=event.get('count', 1)
                )
            elif event['type'] == 'scroll':
                perform_scroll(
                    amount=event['amount']
                )
            elif event['type'] == 'key':
                perform_key_press(
                    event['key']
                )

    except KeyboardInterrupt:
        print("\nReplay stopped by user.")
    finally:
        # Release any remaining held keys
        for k, obj in held_keys.items():
            release_key(obj)
            print(f"Released {k} key")

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


def hold_multiple_keys(keys):
    """
    Hold multiple modifier keys in a specific order.

    Args:
        keys (list): List of modifier keys to hold

    Returns:
        dict: Dictionary mapping key names to their key objects
    """
    # Define the order of modifier keys
    key_order = ['ctrl', 'alt', 'shift', 'cmd', 'win', 'windows']

    # Sort keys based on the defined order
    sorted_keys = sorted(keys, key=lambda k: key_order.index(
        k.lower()) if k.lower() in key_order else len(key_order))

    held_keys = {}
    for key in sorted_keys:
        key_obj = hold_key(key)
        if key_obj:
            held_keys[key] = key_obj
    return held_keys


def release_multiple_keys(held_keys):
    """
    Release multiple held keys in reverse order of holding.

    Args:
        held_keys (dict): Dictionary of held keys from hold_multiple_keys
    """
    # Release keys in reverse order
    for key in reversed(list(held_keys.keys())):
        release_key(held_keys[key])
        print(f"Released {key} key")


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
    held_keys = {}

    # Convert string key to Key object if it's a special key
    if hasattr(Key, key):
        key = getattr(Key, key)
    elif len(key) == 1:
        key = key
    else:
        print(f"Warning: Unknown key '{key}'")
        return

    try:
        # Handle modifiers
        if modifiers:
            held_keys = hold_multiple_keys(modifiers)

        # Press the key the specified number of times
        for _ in range(count):
            keyboard.press(key)
            keyboard.release(key)
            if _ < count - 1:  # Don't sleep after last press
                time.sleep(interval)

    finally:
        # Always release modifier keys, even if an error occurs
        if held_keys:
            release_multiple_keys(held_keys)

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


def hold_key(key):
    """
    Hold down a key.

    Args:
        key (str): Key to hold down (e.g., 'cmd', 'ctrl', 'shift', 'alt')

    Returns:
        Key: Key object that was held down, or None if invalid key
    """
    keyboard = KeyboardController()

    # Map key names to Key objects
    key_map = {
        'cmd': Key.cmd,
        'command': Key.cmd,
        'win': Key.cmd,
        'windows': Key.cmd,
        'ctrl': Key.ctrl,
        'control': Key.ctrl,
        'alt': Key.alt,
        'shift': Key.shift
    }

    # Convert key name to lowercase for case-insensitive matching
    key_lower = key.lower()

    if key_lower in key_map:
        key_obj = key_map[key_lower]
        keyboard.press(key_obj)
        return key_obj
    else:
        print(f"Warning: Unsupported key '{key}' for holding")
        return None


def release_key(key_obj):
    """
    Release a previously held key.

    Args:
        key_obj: Key object to release
    """
    if key_obj is not None:
        keyboard = KeyboardController()
        keyboard.release(key_obj)


def parse_simple_sequence(sequence_str):
    """
    Parse a simple sequence string into a list of action dictionaries.

    Args:
        sequence_str (str): Sequence string in format "action1 param1 param2; action2 param1 param2"

    Returns:
        list: List of action dictionaries
    """
    actions = []
    commands = [cmd.strip() for cmd in sequence_str.split(';')]

    for cmd in commands:
        if not cmd:
            continue

        parts = shlex.split(cmd)  # Properly handle quoted strings
        action_type = parts[0].lower()
        params = parts[1:]

        if action_type == 'move':
            if len(params) >= 2:
                action = {
                    'type': 'move',
                    'x': int(params[0]),
                    'y': int(params[1]),
                    'smooth': '--smooth' in params
                }
                actions.append(action)

        elif action_type == 'click':
            action = {
                'type': 'click',
                'button': params[0] if params and params[0] in ['left', 'right'] else 'left',
                'count': int(params[1]) if len(params) > 1 else 1
            }
            actions.append(action)

        elif action_type == 'key':
            if params:
                action = {
                    'type': 'key',
                    'key': params[0]
                }
                # Check for modifiers
                if len(params) > 1:
                    action['modifiers'] = [mod for mod in params[1:] if mod in
                                           ['ctrl', 'control', 'alt', 'shift', 'cmd', 'command', 'win', 'windows']]
                actions.append(action)

        elif action_type == 'wait':
            if params:
                action = {
                    'type': 'wait',
                    'seconds': float(params[0])
                }
                actions.append(action)

        elif action_type == 'drag':
            if len(params) >= 2:
                action = {
                    'type': 'move',
                    'x': int(params[0]),
                    'y': int(params[1]),
                    'drag': True
                }
                actions.append(action)

        elif action_type == 'drag_from':
            if len(params) >= 4:
                actions.extend([
                    {
                        'type': 'move',
                        'x': int(params[0]),
                        'y': int(params[1])
                    },
                    {
                        'type': 'move',
                        'x': int(params[2]),
                        'y': int(params[3]),
                        'drag': True
                    }
                ])

        elif action_type == 'type':
            if params:
                action = {
                    'type': 'type',
                    'text': params[0]
                }
                # Check for interval parameter
                for i, param in enumerate(params):
                    if param == '--interval' and i + 1 < len(params):
                        action['interval'] = float(params[i + 1])
                actions.append(action)

        elif action_type == 'scroll':
            if params:
                action = {
                    'type': 'scroll',
                    'amount': int(params[0])
                }
                # Check for additional parameters
                for i, param in enumerate(params):
                    if param == '--steps' and i + 1 < len(params):
                        action['steps'] = int(params[i + 1])
                    elif param == '--interval' and i + 1 < len(params):
                        action['interval'] = float(params[i + 1])
                actions.append(action)

    return actions


def list_windows():
    """List all available window titles."""
    system = platform.system()

    if system == "Linux":
        try:
            output = subprocess.check_output(['wmctrl', '-l'], text=True)
            print("\nAvailable Windows:")
            print("=" * 80)
            print(f"{'Window ID':<12} | {'Desktop':<8} | {'Title':<58}")
            print("-" * 80)

            for line in output.split('\n'):
                if not line.strip():
                    continue
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    window_id, desktop, _, title = parts
                    print(f"{window_id:<12} | {desktop:<8} | {title[:58]}")

            print("=" * 80)
        except subprocess.CalledProcessError:
            print("Error: wmctrl is not installed. Please install it using:")
            print("sudo apt-get install wmctrl")

    elif system == "Darwin":  # macOS
        try:
            script = '''
                tell application "System Events"
                    set windowList to {}
                    repeat with proc in (processes where background only is false)
                        set procName to name of proc
                        repeat with w in (windows of proc)
                            set end of windowList to {procName & ": " & name of w}
                        end repeat
                    end repeat
                    return windowList
                end tell
            '''
            output = subprocess.check_output(
                ['osascript', '-e', script], text=True)

            print("\nAvailable Windows:")
            print("=" * 80)
            print(f"{'Application/Window Title':<78}")
            print("-" * 80)

            for line in output.split(', '):
                title = line.strip().strip('"{}')
                if title:
                    print(f"{title[:78]}")

            print("=" * 80)
        except subprocess.CalledProcessError as e:
            print(f"Error listing windows: {e}")

    elif system == "Windows":
        try:
            script = '''
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            public class Win32 {
                [DllImport("user32.dll")]
                public static extern IntPtr GetForegroundWindow();
                
                [DllImport("user32.dll")]
                public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
                
                [DllImport("user32.dll")]
                public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
            }
"@

            Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object ProcessName, MainWindowTitle | Format-Table -AutoSize
            '''
            output = subprocess.check_output(
                ['powershell', '-Command', script], text=True)

            print("\nAvailable Windows:")
            print("=" * 80)
            print(output)
            print("=" * 80)
        except subprocess.CalledProcessError as e:
            print(f"Error listing windows: {e}")

    else:
        print(f"Window listing is not supported on {system}")


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
    record_group.add_argument('--sequence', type=str,
                              help='Execute a sequence of actions (simple syntax or JSON file)')

    # Global options
    global_group = parser.add_argument_group('Global options')
    global_group.add_argument('--global-delay', type=float, default=0,
                              help='Default delay between all actions (default: 0)')
    global_group.add_argument('--global-smooth', action='store_true',
                              help='Enable smooth movement for all move/drag actions')
    global_group.add_argument('--global-duration', type=float, default=1.0,
                              help='Default duration for all smooth movements (default: 1.0)')
    global_group.add_argument('--global-steps', type=int, default=100,
                              help='Default steps for all smooth movements (default: 100)')
    global_group.add_argument('--global-button', choices=['left', 'right'], default='left',
                              help='Default button for all click/drag actions (default: left)')
    global_group.add_argument('--global-interval', type=float, default=0.1,
                              help='Default interval for all multi-actions (default: 0.1)')
    global_group.add_argument('--wait', type=float,
                              help='Wait for specified number of seconds')

    # Mouse movement options
    mouse_group = parser.add_argument_group('Mouse movement options')
    mouse_group.add_argument('--move', nargs=2, type=int, metavar=('X', 'Y'),
                             help='Move mouse to specified X,Y coordinates')
    mouse_group.add_argument('--smooth', action='store_true',
                             help='Move mouse smoothly to target position')
    mouse_group.add_argument('--duration', type=float, default=1.0,
                             help='Duration of smooth movement in seconds (default: 1.0)')
    mouse_group.add_argument('--steps', type=int, default=100,
                             help='Number of steps in smooth movement (default: 100)')
    mouse_group.add_argument('--delay', type=float, default=0,
                             help='Delay before moving in seconds (default: 0)')
    mouse_group.add_argument('--monitor-index', type=int,
                             help='Index of monitor to use for coordinates')
    mouse_group.add_argument('--ignore-bounds', action='store_true',
                             help='Ignore screen boundary checks')

    # Click options
    click_group = parser.add_argument_group('Click options')
    click_group.add_argument('--click', action='store_true',
                             help='Perform a left click')
    click_group.add_argument('--right-click', action='store_true',
                             help='Perform a right click')
    click_group.add_argument('--double-click', action='store_true',
                             help='Perform a double click')
    click_group.add_argument('--click-count', type=int, default=1,
                             help='Number of clicks to perform (default: 1)')
    click_group.add_argument('--click-interval', type=float, default=0.1,
                             help='Interval between clicks in seconds (default: 0.1)')
    click_group.add_argument('--click-delay', type=float, default=0,
                             help='Delay after clicking in seconds (default: 0)')

    # Drag options
    drag_group = parser.add_argument_group('Drag options')
    drag_group.add_argument('--drag', nargs=2, type=int, metavar=('DX', 'DY'),
                            help='Drag to specified coordinates')
    drag_group.add_argument('--drag-from', nargs=4, type=int, metavar=('X1', 'Y1', 'X2', 'Y2'),
                            help='Drag from X1,Y1 to X2,Y2')
    drag_group.add_argument('--no-drag-smooth', action='store_true',
                            help='Disable smooth movement during drag')
    drag_group.add_argument('--click-before-drag', action='store_true',
                            help='Click before starting drag')
    drag_group.add_argument('--click-after-drag', action='store_true',
                            help='Click after completing drag')

    # Key options
    key_group = parser.add_argument_group('Key options')
    key_group.add_argument('--hold-key', choices=['cmd', 'ctrl', 'alt', 'shift'],
                           help='Hold down a modifier key')
    key_group.add_argument('--release-key', action='store_true',
                           help='Release the currently held key')
    key_group.add_argument('--key', action='append',
                           help='Press a key (e.g., a, enter, space, tab, f1-f12, etc.)')
    key_group.add_argument('--modifiers', nargs='+',
                           choices=['ctrl', 'control', 'alt', 'shift',
                                    'cmd', 'command', 'win', 'windows'],
                           help='Modifier keys to hold while pressing the key')
    key_group.add_argument('--key-count', type=int, default=1,
                           help='Number of times to press the key (default: 1)')
    key_group.add_argument('--key-interval', type=float, default=0.1,
                           help='Interval between key presses in seconds (default: 0.1)')
    key_group.add_argument('--key-delay', type=float, default=0,
                           help='Delay after key press in seconds (default: 0)')

    # Type options
    type_group = parser.add_argument_group('Type options')
    type_group.add_argument('--type', type=str,
                            help='Type a sequence of text')
    type_group.add_argument('--type-interval', type=float, default=0.05,
                            help='Interval between keystrokes when typing (default: 0.05)')
    type_group.add_argument('--type-delay', type=float, default=0,
                            help='Delay after typing in seconds (default: 0)')

    # Scroll options
    scroll_group = parser.add_argument_group('Scroll options')
    scroll_group.add_argument('--scroll', type=int,
                              help='Amount to scroll (positive for up, negative for down)')
    scroll_group.add_argument('--scroll-steps', type=int, default=10,
                              help='Number of steps to divide the scroll into (default: 10)')
    scroll_group.add_argument('--scroll-interval', type=float, default=0.01,
                              help='Time between scroll steps in seconds (default: 0.01)')
    scroll_group.add_argument('--scroll-delay', type=float, default=0,
                              help='Delay after scrolling in seconds (default: 0)')

    # Monitor options
    monitor_group = parser.add_argument_group('Monitor options')
    monitor_group.add_argument('--monitor', action='store_true',
                               help='Monitor mouse position in real-time')
    monitor_group.add_argument('--monitor-interval', type=float, default=0.1,
                               help='Update interval for monitoring in seconds (default: 0.1)')
    monitor_group.add_argument('--monitor-duration', type=float,
                               help='Duration to monitor in seconds (default: indefinite)')
    monitor_group.add_argument('--no-monitor-clicks', action='store_true',
                               help='Disable click detection during monitoring')
    monitor_group.add_argument('--list-monitors', action='store_true',
                               help='List all detected monitors')

    # Window selection options
    window_group = parser.add_argument_group('Window selection options')
    window_group.add_argument('--list-windows', action='store_true',
                              help='List all available window titles')
    window_group.add_argument('--window-title', type=str,
                              help='Select window by title (exact or partial match)')
    window_group.add_argument('--window-process', type=str,
                              help='Select window by process name')
    window_group.add_argument('--window-wait', type=float, default=1.0,
                              help='Wait time after window activation (default: 1.0)')
    window_group.add_argument('--no-window-required', action='store_true',
                              help='Continue even if window is not found')
    window_group.add_argument('--window-retry', type=int, default=3,
                              help='Number of times to retry finding window (default: 3)')

    args = parser.parse_args()

    # Handle monitor listing
    if args.list_monitors:
        list_monitors()
        return

    # Handle monitor mode
    if args.monitor:
        monitor_mouse_position(
            update_interval=args.monitor_interval,
            show_clicks=not args.no_monitor_clicks,
            duration=args.monitor_duration
        )
        return

    # Handle record mode
    if args.record is not None:
        record_events(args.record, args.record_duration)
        return

    # Handle replay mode
    if args.replay is not None:
        replay_events(args.replay)
        return

    # Handle sequence mode
    if args.sequence is not None:
        if args.sequence.endswith('.json') and os.path.isfile(args.sequence):
            with open(args.sequence, 'r') as f:
                actions = json.load(f)
        elif args.sequence.startswith('[') and args.sequence.endswith(']'):
            actions = json.loads(args.sequence)
        else:
            # Parse simple sequence syntax
            actions = parse_simple_sequence(args.sequence)
        perform_sequence(actions)
        return

    # Handle window selection
    if args.window_title or args.window_process:
        if not find_and_activate_window(
            title=args.window_title,
            process=args.window_process,
            wait=args.window_wait,
            required=not args.no_window_required,
            retry_count=args.window_retry
        ):
            return

    # Handle window listing
    if args.list_windows:
        list_windows()
        return

    # Handle mouse movement
    if args.move is not None:
        x, y = args.move
        move_mouse(
            x, y,
            delay=args.delay,
            check_bounds=not args.ignore_bounds,
            smooth=args.smooth or args.global_smooth,
            smooth_duration=args.duration if not args.global_smooth else args.global_duration,
            smooth_steps=args.steps if not args.global_smooth else args.global_steps,
            monitor_index=args.monitor_index
        )

    # Handle clicks
    if args.click or args.right_click or args.double_click:
        button = 'right' if args.right_click else args.global_button
        perform_click(
            button=button,
            count=2 if args.double_click else args.click_count,
            interval=args.click_interval if not args.global_interval else args.global_interval,
            double=args.double_click,
            delay_after=args.click_delay
        )

    # Handle drag operations
    if args.drag is not None or args.drag_from is not None:
        if args.drag_from is not None:
            x1, y1, x2, y2 = args.drag_from
            move_mouse(x1, y1, smooth=not args.no_drag_smooth)
            if args.click_before_drag:
                perform_click(button=args.global_button)
            move_mouse(x2, y2, smooth=not args.no_drag_smooth)
            if args.click_after_drag:
                perform_click(button=args.global_button)
        else:
            dx, dy = args.drag
            if args.click_before_drag:
                perform_click(button=args.global_button)
            move_mouse(dx, dy, smooth=not args.no_drag_smooth)
            if args.click_after_drag:
                perform_click(button=args.global_button)

    # Handle key operations
    if args.key:
        for key in args.key:
            perform_key_press(
                key,
                modifiers=args.modifiers,
                count=args.key_count,
                interval=args.key_interval if not args.global_interval else args.global_interval,
                delay_after=args.key_delay
            )

    # Handle text typing
    if args.type:
        perform_type(
            args.type,
            interval=args.type_interval,
            delay_after=args.type_delay
        )

    # Handle scrolling
    if args.scroll is not None:
        perform_scroll(
            args.scroll,
            steps=args.scroll_steps,
            interval=args.scroll_interval,
            delay_after=args.scroll_delay
        )

    # Handle wait command
    if args.wait is not None:
        print(f"Waiting {args.wait} seconds...")
        time.sleep(args.wait)


if __name__ == "__main__":
    main()
