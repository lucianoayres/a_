# a\_

A simple Python utility to move the mouse cursor to specified coordinates and perform mouse actions using command line arguments.

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/a_.git
   cd a_
   ```

2. Set up a virtual environment (recommended):

   ```
   # Make the setup script executable
   chmod +x setup_venv.sh

   # Run the setup script
   ./setup_venv.sh
   ```

   This will:

   - Create a virtual environment in a `venv` directory
   - Activate the virtual environment
   - Install the required dependencies from requirements.txt

   Alternatively, you can set up the virtual environment manually:

   ```
   # Create virtual environment
   python3 -m venv venv

   # Activate virtual environment
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   ```

3. To activate the virtual environment in the future:

   ```
   source venv/bin/activate
   ```

4. To deactivate the virtual environment when done:
   ```
   deactivate
   ```

## Usage

### New Command-Line Interface

The utility supports a semantic command-line interface that allows you to specify actions in sequence with their own parameters.

#### Basic Usage with --move

Move the mouse to specified coordinates:

```
python a_.py --move 500 300
```

This will move the mouse cursor to the position with X=500 and Y=300.

#### Sequential Actions

You can combine multiple actions in a single command:

```
python a_.py --move 500 300 --click --type "Hello, world!" --key enter
```

This will:

1. Move the mouse to (500, 300)
2. Perform a left click
3. Type "Hello, world!"
4. Press the Enter key

#### Global Parameters

You can set global parameters that apply to all actions:

```
python a_.py --global-smooth --global-delay 0.5 --move 500 300 --move 600 400 --move 700 500
```

This will:

1. Move the mouse smoothly to (500, 300)
2. Wait 0.5 seconds
3. Move the mouse smoothly to (600, 400)
4. Wait 0.5 seconds
5. Move the mouse smoothly to (700, 500)

Available global parameters:

- `--global-delay SECONDS`: Default delay between all actions (default: 0)
- `--global-smooth`: Enable smooth movement for all move/drag actions
- `--global-duration SECONDS`: Default duration for all smooth movements (default: 1.0)
- `--global-steps COUNT`: Default steps for all smooth movements (default: 100)
- `--global-button [left|right]`: Default button for all click/drag actions (default: left)
- `--global-interval SECONDS`: Default interval for all multi-actions (clicks, key presses) (default: 0.1)

#### Action-Specific Parameters

Each action can have its own specific parameters that override global settings:

```
python a_.py --global-smooth --move 500 300 --move 600 400 --smooth --duration 2.0 --move 700 500
```

In this example, all movements are smooth, but the second movement has a custom duration of 2.0 seconds.

### Mouse Movement Examples

#### Basic Movement

```
# Move to coordinates
python a_.py --move 500 300

# Move smoothly
python a_.py --move 500 300 --smooth

# Move with custom smooth movement parameters
python a_.py --move 500 300 --smooth --duration 2.0 --steps 150

# Move with delay before movement
python a_.py --move 500 300 --delay 1.5

# Move and ignore screen boundary checks
python a_.py --move 2000 1500 --ignore-bounds
```

#### Multiple Movements

```
# Multiple movements in sequence
python a_.py --move 500 300 --move 600 400 --move 700 500

# Multiple smooth movements with global settings
python a_.py --global-smooth --global-duration 0.5 --move 500 300 --move 600 400 --move 700 500

# Multiple movements with waits in between
python a_.py --move 500 300 --wait 1 --move 600 400 --wait 1 --move 700 500
```

### Mouse Click Examples

#### Basic Clicks

```
# Move and left click
python a_.py --move 500 300 --click

# Move and right click
python a_.py --move 500 300 --right-click

# Move and double click
python a_.py --move 500 300 --double-click

# Click without moving (at current position)
python a_.py --click
```

#### Advanced Click Options

```
# Multiple clicks
python a_.py --move 500 300 --click --click-count 3

# Multiple clicks with custom interval
python a_.py --move 500 300 --click --click-count 3 --click-interval 0.2

# Click with delay after
python a_.py --move 500 300 --click --click-delay 1.5
```

### Drag Operation Examples

#### Basic Drag Operations

```
# Move to a position and drag to another position
python a_.py --move 100 100 --drag 300 300

# Drag directly from one position to another
python a_.py --drag-from 100 100 300 300

# Drag without smooth movement
python a_.py --move 100 100 --drag 300 300 --no-drag-smooth
```

#### Advanced Drag Operations

```
# Click before dragging
python a_.py --move 100 100 --drag 300 300 --click-before-drag

# Click after dragging
python a_.py --move 100 100 --drag 300 300 --click-after-drag

# Click before and after dragging
python a_.py --move 100 100 --drag 300 300 --click-before-drag --click-after-drag

# Drag with custom smooth movement parameters
python a_.py --move 100 100 --drag 300 300 --duration 2.0 --steps 150
```

### Keyboard Examples

#### Basic Key Presses

```
# Press a key
python a_.py --key a

# Press a special key
python a_.py --key enter

# Press a key with modifier
python a_.py --key c --modifiers ctrl

# Press a key with multiple modifiers
python a_.py --key s --modifiers ctrl shift
```

#### Advanced Key Press Options

```
# Multiple key presses
python a_.py --key space --key-count 5

# Multiple key presses with custom interval
python a_.py --key space --key-count 5 --key-interval 0.2

# Key press with delay after
python a_.py --key tab --key-delay 1.5

# Key press after mouse movement
python a_.py --move 500 300 --key enter
```

### Text Typing Examples

```
# Type text
python a_.py --type "Hello, world!"

# Type text with custom interval
python a_.py --type "Hello, world!" --type-interval 0.1

# Type text with delay after
python a_.py --type "Hello, world!" --type-delay 1.5

# Move, click, and type
python a_.py --move 500 300 --click --type "Hello, world!"
```

### Wait Examples

```
# Wait between actions
python a_.py --move 500 300 --wait 2 --click

# Multiple waits
python a_.py --move 500 300 --wait 1 --click --wait 2 --key enter
```

### Scroll Examples

You can scroll up or down at the current mouse position:

```
# Scroll up by 10 units
python a_.py --scroll 10

# Scroll down by 5 units
python a_.py --scroll -5

# Scroll with custom parameters
python a_.py --scroll 20 --scroll-steps 20 --scroll-interval 0.02

# Move to a position and then scroll
python a_.py --move 500 300 --scroll 10

# Move, click, and then scroll
python a_.py --move 500 300 --click --scroll 10
```

#### Scroll Options

Customize the scroll behavior with these options:

- `--scroll AMOUNT`: Amount to scroll (positive for up, negative for down)
- `--scroll-steps COUNT`: Number of steps to divide the scroll into (default: 10)
- `--scroll-interval SECONDS`: Time between scroll steps in seconds (default: 0.01)
- `--scroll-delay SECONDS`: Delay in seconds after scrolling (default: 0)

### Complex Sequence Examples

#### Form Filling Example

```
# Fill out a form
python a_.py --move 500 300 --click --type "John Doe" --key tab --type "john.doe@example.com" --key tab --type "password123" --key tab --key space
```

#### Drawing Example

```
# Draw a square
python a_.py --move 100 100 --drag 300 100 --drag 300 300 --drag 100 300 --drag 100 100
```

#### Text Editing Example

```
# Select all text and replace it
python a_.py --move 500 300 --click --key a --modifiers ctrl --type "New text" --key s --modifiers ctrl
```

#### Web Browsing Example

```
# Navigate to a website and search
python a_.py --move 500 50 --click --type "https://www.google.com" --key enter --wait 2 --move 500 300 --click --type "python automation" --key enter
```

### Using the Run Script with New Interface

```
# Basic movement
./run.sh --move 500 300

# Complex sequence
./run.sh --move 500 300 --click --type "Hello, world!" --key enter

# Global parameters
./run.sh --global-smooth --move 500 300 --move 600 400 --move 700 500
```

### Mouse Position Monitor

You can monitor the real-time position of your mouse cursor on the screen:

```
python a_.py --monitor
```

This will display a continuously updating table showing:

- Current time elapsed
- X and Y coordinates
- Number of left and right clicks

The monitor can be stopped by pressing Ctrl+C.

#### Monitor Options

Customize the monitor behavior with these options:

```
# Set update interval to 0.5 seconds
python a_.py --monitor --monitor-interval 0.5

# Monitor for a specific duration (10 seconds)
python a_.py --monitor --monitor-duration 10

# Disable click detection
python a_.py --monitor --no-monitor-clicks
```

Examples:

```
# Basic monitoring
./run.sh --monitor

# Monitor with 0.2s update interval for 30 seconds
./run.sh --monitor --monitor-interval 0.2 --monitor-duration 30

# Monitor position only (no click detection)
./run.sh --monitor --no-monitor-clicks
```

### Multi-Monitor Support

The utility supports working with multiple monitors. You can list all detected monitors, and specify which monitor to use for your automation tasks.

#### Listing Monitors

To see all detected monitors and their properties:

```
python a_.py --list-monitors
```

This will display a table showing:

- Monitor index
- Monitor name
- Resolution
- Position (offset from the primary monitor)
- Whether it's the primary monitor

#### Targeting a Specific Monitor

By default, coordinates are relative to the primary monitor. To target a specific monitor:

```
python a_.py --monitor-index 1 --move 500 300
```

This will move the mouse to coordinates (500, 300) on monitor with index 1. The coordinates are relative to the top-left corner of the specified monitor.

#### Examples

```
# List all monitors
python a_.py --list-monitors

# Move to position on the primary monitor
python a_.py --move 500 300

# Move to position on the second monitor
python a_.py --monitor-index 1 --move 500 300

# Click on the third monitor
python a_.py --monitor-index 2 --move 500 300 --click

# Drag on a specific monitor
python a_.py --monitor-index 1 --move 100 100 --drag 300 300

# Complex sequence on a specific monitor
python a_.py --monitor-index 1 --move 500 300 --click --type "Hello" --key tab
```

#### Using with Sequences

When using the `--sequence` parameter with JSON, you can specify the monitor index for each move action:

```json
[
  {
    "type": "move",
    "x": 500,
    "y": 300,
    "monitor_index": 1,
    "smooth": true
  },
  {
    "type": "click",
    "button": "left"
  }
]
```

### Mouse Clicks

You can add mouse clicks after the movement by adding click options:

```
python a_.py --move X Y --click       # Left mouse button click
python a_.py --move X Y --right-click # Right mouse button click
```

#### Multiple Clicks

Perform multiple clicks with a specified interval:

```
python a_.py --move X Y --click --click-count 3 --click-interval 0.2
```

This will perform 3 left clicks with a 0.2 second interval between each click.

#### Double-Click

For double-clicks:

```
python a_.py --move X Y --double-click
```

Or alternatively:

```
python a_.py --move X Y --click --double
```

The `--double` flag overrides the `--click-count` parameter.

#### Click Delay

Add a delay after clicking:

```
python a_.py --move X Y --click --click-delay 1.5
```

Examples:

```
# Move to (500, 300) and left-click
./run.sh --move 500 300 --click

# Move to (800, 400) and right-click
./run.sh --move 800 400 --right-click
```

### Drag Operations

You can perform drag operations by specifying start and end coordinates:

```
python a_.py --move X Y --drag DX DY
```

Where:

- `X` and `Y` are the starting coordinates
- `DX` and `DY` are the ending coordinates

Alternatively, you can specify both start and end coordinates in a single command:

```
python a_.py --drag-from X1 Y1 X2 Y2
```

Where:

- `X1` and `Y1` are the starting coordinates
- `X2` and `Y2` are the ending coordinates

#### Selecting the Drag Button

By default, the left mouse button is used for dragging. You can specify which button to use:

```
python a_.py --move X Y --drag DX DY                # Left button drag (default)
python a_.py --move X Y --click --drag DX DY        # Left button drag (explicit)
python a_.py --move X Y --right-click --drag DX DY  # Right button drag
```

#### Smooth Dragging

Drag with smooth movement (default) or disable it:

```
python a_.py --move X Y --drag DX DY                # Smooth drag (default)
python a_.py --move X Y --drag DX DY --no-drag-smooth  # Direct drag
```

#### Click and Drag Combinations

You can combine clicks with drag operations:

```
# Click before starting the drag operation
python a_.py --move X Y --drag DX DY --click-before-drag

# Click after completing the drag operation
python a_.py --move X Y --drag DX DY --click-after-drag

# Click both before and after the drag operation
python a_.py --move X Y --drag DX DY --click-before-drag --click-after-drag
```

All click options (count, interval, double, delay) apply to these clicks as well.

Examples:

```
# Drag from (100, 100) to (300, 300) with left button (default)
python a_.py --move 100 100 --drag 300 300

# Drag from (200, 200) to (400, 400) with right button
python a_.py --move 200 200 --right-click --drag 400 400

# Drag from (100, 100) to (300, 300) without smooth movement
python a_.py --move 100 100 --drag 300 300 --no-drag-smooth

# Left-click, then drag from (100, 100) to (300, 300) with left button
python a_.py --move 100 100 --drag 300 300 --click-before-drag

# Drag from (100, 100) to (300, 300) with left button, then left-click
python a_.py --move 100 100 --drag 300 300 --click-after-drag

# Double-click with left button, drag from (100, 100) to (300, 300), then click again
python a_.py --move 100 100 --drag 300 300 --click-before-drag --click-after-drag --double

# Double-click with right button, drag from (100, 100) to (300, 300) with right button, then right-click again
python a_.py --move 100 100 --drag 300 300 --click-before-drag --click-after-drag --double --right-click
```

### Keyboard Key Press

You can simulate keyboard key presses with optional modifier keys:

```
python a_.py --key KEY [--modifiers MOD1 MOD2 ...] [options]
```

Where:

- `KEY` is the key to press (e.g., 'a', 'enter', 'space', etc.)
- `MOD1`, `MOD2`, etc. are optional modifier keys to hold while pressing the key (e.g., 'ctrl', 'shift', 'alt')

#### Supported Keys

The following special keys are supported:

- Navigation: `enter`, `esc`, `escape`, `space`, `tab`, `backspace`, `delete`
- Arrow keys: `up`, `down`, `left`, `right`
- Navigation: `home`, `end`, `page_up`, `page_down`
- Function keys: `f1` through `f12`
- Any single character key (e.g., 'a', 'b', '1', '2', etc.)

#### Supported Modifiers

The following modifier keys are supported:

- `ctrl` or `control`
- `alt`
- `shift`
- `cmd`, `command`, `win`, or `windows` (Command key on macOS, Windows key on Windows)

#### Multiple Key Presses

Perform multiple key presses with a specified interval:

```
python a_.py --key KEY --key-count COUNT --key-interval INTERVAL
```

This will perform the specified number of key presses with the given interval between each press.

#### Key Press Delay

Add a delay after key presses:

```
python a_.py --key KEY --key-delay SECONDS
```

Examples:

```
# Press the 'a' key
python a_.py --key a

# Press Enter
python a_.py --key enter

# Press Ctrl+C
python a_.py --key c --modifiers ctrl

# Press Ctrl+Alt+Delete
python a_.py --key delete --modifiers ctrl alt

# Press Shift+F5
python a_.py --key f5 --modifiers shift

# Press the spacebar 5 times with 0.2s interval
python a_.py --key space --key-count 5 --key-interval 0.2

# Press Tab and wait 2 seconds after
python a_.py --key tab --key-delay 2

# Press Ctrl+S
python a_.py --key s --modifiers ctrl
```

### Text Typing

You can type a sequence of text characters:

```
python a_.py --type "TEXT" [options]
```

Options:

- `--type-interval SECONDS`: Time between key presses when typing (default: 0.05)
- `--type-delay SECONDS`: Delay in seconds after typing (default: 0)

Examples:

```
# Type "Hello, world!"
python a_.py --type "Hello, world!"

# Type "Hello" with a slower typing speed
python a_.py --type "Hello" --type-interval 0.1

# Type "Done!" and wait 2 seconds after
python a_.py --type "Done!" --type-delay 2
```

### Sequential Actions

You can perform a sequence of actions in a single command using the sequence options:

#### Simple Action Sequences

The simplest way to perform a sequence of actions is using the `--sequence` parameter with a simplified string syntax:

```
python a_.py --sequence "move 100 100; click left; wait 1; key enter; move 200 200; drag 300 300"
```

The sequence is a semicolon-separated list of actions, where each action has a command and parameters.

Available commands:

- `move X Y [--smooth]` - Move to coordinates X,Y
- `click [left|right] [count]` - Click with specified button and count
- `key KEY [modifiers...]` - Press a key with optional modifiers
- `wait SECONDS` - Wait for specified seconds
- `drag X Y` - Drag from current position to X,Y
- `drag_from X1 Y1 X2 Y2` - Drag from X1,Y1 to X2,Y2
- `type "TEXT" [--interval=SECONDS]` - Type a sequence of text with optional typing speed
- `scroll AMOUNT [--steps=COUNT] [--interval=SECONDS]` - Scroll up (positive) or down (negative)

This syntax supports all the main action types available in the program but with a more concise format. While it doesn't support every parameter that the JSON format does, it covers the most commonly used options for each action type.

#### Advanced Sequences with JSON

For more complex sequences of actions with full parameter control, you can use the `--sequence` parameter with a JSON string or file:

```
python a_.py --sequence '[{"type":"move","x":500,"y":300},{"type":"click","button":"left"}]'
# or
python a_.py --sequence path/to/sequence.json
```

The JSON should contain an array of action objects, each with a `type` field and appropriate parameters. This format provides access to all parameters supported by the program for each action type.

Example JSON sequence:

```json
[
  {
    "type": "move",
    "x": 500,
    "y": 300,
    "smooth": true
  },
  {
    "type": "click",
    "button": "left",
    "count": 2
  },
  {
    "type": "wait",
    "seconds": 1.5
  },
  {
    "type": "key",
    "key": "a",
    "modifiers": ["ctrl", "shift"]
  },
  {
    "type": "scroll",
    "amount": 10,
    "steps": 15,
    "interval": 0.02
  },
  {
    "type": "move",
    "x": 700,
    "y": 400
  },
  {
    "type": "drag_to",
    "x": 900,
    "y": 600
  }
]
```

This provides the most flexibility for complex automation tasks.

### Global Options

You can set global options that apply to all actions in a sequence:

```
python a_.py --global-delay 0.5 --global-smooth --global-button right [other options]
```

Available global options:

- `--global-delay SECONDS` - Add a delay between all actions
- `--global-smooth` - Enable smooth movement for all move/drag actions
- `--global-duration SECONDS` - Set default duration for all smooth movements
- `--global-steps COUNT` - Set default steps for all smooth movements
- `--global-button [left|right]` - Set default button for all click/drag actions
- `--global-interval SECONDS` - Set default interval for all multi-actions

### Shell Script Wrapper

For convenience, a shell script wrapper is provided that activates the virtual environment and runs the script:

```
./run.sh [arguments]
```

Examples:

```
# Move to (500, 300)
./run.sh --move 500 300

# Move to (500, 300) and left-click
./run.sh --move 500 300 --click

# Move to (800, 400) and right-click
./run.sh --move 800 400 --right-click

# Perform multiple clicks
./run.sh --move 500 300 --click --click-count 3 --click-interval 0.2

# Perform a drag operation
./run.sh --move 100 100 --drag 300 300

# Click, then drag, then click again
./run.sh --move 100 100 --drag 300 300 --click-before-drag --click-after-drag

# Double-click with right button, drag with right button, then right-click again
./run.sh --move 100 100 --drag 300 300 --click-before-drag --click-after-drag --double --right-click

# Monitor mouse position
./run.sh --monitor
```

## Making the Script Executable (Linux/macOS)

You can make the script executable to run it directly:

```
chmod +x a_.py
./a_.py [options]
```

## Requirements

- Python 3.6 or higher
- pynput 1.7.6
