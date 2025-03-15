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

### Basic Usage

Move the mouse to specified coordinates:

```
python a_.py X Y
```

Where:

- `X` is the X coordinate (horizontal position)
- `Y` is the Y coordinate (vertical position)

Example:

```
python a_.py 500 300
```

This will move the mouse cursor to the position with X=500 and Y=300.

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

### Mouse Clicks

You can add mouse clicks after the movement by adding click options:

```
python a_.py X Y --left-click    # Left mouse button click
python a_.py X Y --right-click   # Right mouse button click
```

#### Multiple Clicks

Perform multiple clicks with a specified interval:

```
python a_.py X Y --left-click --click-count 3 --click-interval 0.2
```

This will perform 3 left clicks with a 0.2 second interval between each click.

#### Double-Click

For double-clicks:

```
python a_.py X Y --left-click --double
```

The `--double` flag overrides the `--click-count` parameter.

#### Click Delay

Add a delay after clicking:

```
python a_.py X Y --left-click --click-delay 1.5
```

Examples:

```
# Move to (500, 300) and left-click
python a_.py 500 300 --left-click

# Move to (800, 400) and right-click
python a_.py 800 400 --right-click

# Move to (500, 300) and double left-click
python a_.py 500 300 --left-click --double

# Move to (800, 400), right-click, and wait 2 seconds after clicking
python a_.py 800 400 --right-click --click-delay 2

# Move to (500, 300) and perform 5 left clicks with 0.3s interval
python a_.py 500 300 --left-click --click-count 5 --click-interval 0.3
```

### Drag Operations

You can perform drag operations by specifying start and end coordinates:

```
python a_.py X Y --drag-to-x DX --drag-to-y DY
```

Where:

- `X` and `Y` are the starting coordinates
- `DX` and `DY` are the ending coordinates

#### Selecting the Drag Button

By default, the left mouse button is used for dragging. You can specify which button to use:

```
python a_.py X Y --drag-to-x DX --drag-to-y DY                # Left button drag (default)
python a_.py X Y --left-click --drag-to-x DX --drag-to-y DY   # Left button drag (explicit)
python a_.py X Y --right-click --drag-to-x DX --drag-to-y DY  # Right button drag
```

The `--left-click` or `--right-click` flag determines which button is used for both dragging and any associated clicks.

#### Smooth Dragging

Drag with smooth movement (default) or disable it:

```
python a_.py X Y --drag-to-x DX --drag-to-y DY                # Smooth drag (default)
python a_.py X Y --drag-to-x DX --drag-to-y DY --no-drag-smooth  # Direct drag
```

#### Click and Drag Combinations

You can combine clicks with drag operations:

```
# Click before starting the drag operation
python a_.py X Y --drag-to-x DX --drag-to-y DY --click-before-drag

# Click after completing the drag operation
python a_.py X Y --drag-to-x DX --drag-to-y DY --click-after-drag

# Click both before and after the drag operation
python a_.py X Y --drag-to-x DX --drag-to-y DY --click-before-drag --click-after-drag
```

These options use the same button as specified by `--left-click` or `--right-click` (left button by default). All click options (count, interval, double, delay) apply to these clicks as well.

Examples:

```
# Drag from (100, 100) to (300, 300) with left button (default)
python a_.py 100 100 --drag-to-x 300 --drag-to-y 300

# Drag from (200, 200) to (400, 400) with right button
python a_.py 200 200 --right-click --drag-to-x 400 --drag-to-y 400

# Drag from (100, 100) to (300, 300) without smooth movement
python a_.py 100 100 --drag-to-x 300 --drag-to-y 300 --no-drag-smooth

# Left-click, then drag from (100, 100) to (300, 300) with left button
python a_.py 100 100 --drag-to-x 300 --drag-to-y 300 --click-before-drag

# Drag from (100, 100) to (300, 300) with left button, then left-click
python a_.py 100 100 --drag-to-x 300 --drag-to-y 300 --click-after-drag

# Double-click with left button, drag from (100, 100) to (300, 300), then click again
python a_.py 100 100 --drag-to-x 300 --drag-to-y 300 --click-before-drag --click-after-drag --double

# Double-click with right button, drag from (100, 100) to (300, 300) with right button, then right-click again
python a_.py 100 100 --drag-to-x 300 --drag-to-y 300 --click-before-drag --click-after-drag --double --right-click
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

The simplest way to perform a sequence of actions is using the `--do` option with a semicolon-separated list of actions:

```
python a_.py --do "action1; action2; action3"
```

Supported actions:

- `move X Y [--smooth]` - Move to coordinates X,Y with optional smooth movement
- `click [left|right] [count] [--double]` - Click with specified button and count
- `key KEY [modifiers...]` - Press a key with optional modifiers
- `wait SECONDS` - Wait for specified seconds
- `drag X Y [options]` - Drag from current position to X,Y
- `drag_from X1 Y1 X2 Y2 [options]` - Drag from X1,Y1 to X2,Y2
- `type "TEXT" [--interval=SECONDS]` - Type a sequence of text with optional typing speed

Drag options:

- `--no-smooth` - Disable smooth movement during drag
- `--click-before` - Perform a click before starting the drag
- `--click-after` - Perform a click after completing the drag

Examples:

```
# Move to (1298, 993), left-click, then press 'a'
python a_.py --do "move 1298 993; click left; key a"

# Move to (500, 300), wait 1 second, right-click, then press Enter
python a_.py --do "move 500 300; wait 1; click right; key enter"

# Move to (800, 600), left-click, then press Ctrl+S
python a_.py --do "move 800 600; click left; key s ctrl"

# Move smoothly to (1000, 500), double-click, wait 0.5 seconds, then press Escape
python a_.py --do "move 1000 500 --smooth; click left --double; wait 0.5; key escape"

# Move to (100, 100) and drag to (300, 300)
python a_.py --do "move 100 100; drag 300 300"

# Move to (100, 100), click before dragging, drag to (300, 300), then click after
python a_.py --do "move 100 100; drag 300 300 --click-before --click-after"

# Drag directly from (100, 100) to (300, 300) without smooth movement
python a_.py --do "drag_from 100 100 300 300 --no-smooth"

# Move to (500, 300), click, then type "Hello, world!"
python a_.py --do "move 500 300; click left; type \"Hello, world!\""

# Type text with a custom typing speed
python a_.py --do "type \"This is slower text\" --interval=0.1"
```

This syntax is more flexible and concise than using multiple specialized command-line options.

#### Move and Then Press a Key

To move the mouse to coordinates and then press a key:

```
python a_.py X Y --then-key KEY [--modifiers MOD1 MOD2 ...] [options]
```

Example:

```
# Move to (1298, 993) and then press 'a'
python a_.py 1298 993 --then-key a

# Move to (500, 300) and then press Enter
python a_.py 500 300 --then-key enter

# Move to (800, 600) and then press Ctrl+S
python a_.py 800 600 --then-key s --modifiers ctrl
```

#### Adding a Wait Between Actions

You can add a wait between the mouse movement and key press:

```
python a_.py X Y --then-key KEY --then-wait SECONDS
```

Example:

```
# Move to (1298, 993), wait 2 seconds, then press 'a'
python a_.py 1298 993 --then-key a --then-wait 2
```

#### Move and Then Click

To move the mouse to coordinates and then click:

```
python a_.py X Y --then-click [left|right] [options]
```

Example:

```
# Move to (1298, 993) and then left-click
python a_.py 1298 993 --then-click left

# Move to (500, 300), wait 1 second, then right-click
python a_.py 500 300 --then-click right --then-wait 1
```

#### Move, Click, and Then Press a Key

To move the mouse to coordinates, click, and then press a key:

```
python a_.py X Y --then-key KEY --click-before-key [left|right] [options]
```

Example:

```
# Move to (1298, 993), left-click, then press 'a'
python a_.py 1298 993 --then-key a --click-before-key left

# Move to (500, 300), right-click, then press Enter
python a_.py 500 300 --then-key enter --click-before-key right

# Move to (800, 600), left-click, wait 1 second, then press Ctrl+S
python a_.py 800 600 --then-key s --modifiers ctrl --click-before-key left --then-wait 1
```

You can combine this with other options like `--then-wait` to add delays between actions.

#### Advanced Sequences with JSON

For more complex sequences, you can define a JSON sequence of actions:

```
python a_.py --sequence '[{"type":"move","x":1298,"y":993},{"type":"key","key":"a"}]'
```

Or use a JSON file:

```
python a_.py --sequence sequence.json
```

Where `sequence.json` contains:

```json
[
  {
    "type": "move",
    "x": 1298,
    "y": 993,
    "smooth": true
  },
  {
    "type": "wait",
    "seconds": 1.5
  },
  {
    "type": "key",
    "key": "a",
    "count": 3,
    "interval": 0.2
  }
]
```

Supported action types:

- `move`: Move the mouse to coordinates
- `key`: Press a keyboard key
- `click`: Perform a mouse click
- `wait`: Wait for a specified time

### Movement Options

#### Delay Before Movement

You can add a delay before the mouse movement:

```
python a_.py X Y -d SECONDS
```

or

```
python a_.py X Y --delay SECONDS
```

Example:

```
python a_.py 500 300 -d 2
```

This will wait for 2 seconds and then move the mouse cursor to the position with X=500 and Y=300.

#### Smooth Movement

You can enable smooth movement to make the mouse transition gradually to the target coordinates:

```
python a_.py X Y --smooth
```

This will move the mouse smoothly from its current position to the target coordinates.

You can customize the smooth movement with these additional options:

- `--duration SECONDS`: Set the duration of the smooth movement (default: 1.0 second)
- `--steps NUMBER`: Set the number of steps for the smooth movement (default: 100)

Example:

```
python a_.py 500 300 --smooth --duration 2.5 --steps 150
```

This will move the mouse smoothly to position (500, 300) over 2.5 seconds using 150 intermediate steps.

Combine smooth movement with clicks or drags:

```
python a_.py 500 300 --smooth --left-click
python a_.py 100 100 --smooth --drag-to-x 300 --drag-to-y 300
```

#### Screen Resolution Awareness

The script detects your screen resolution and warns you if the coordinates are outside the screen boundaries. You can:

- View your screen resolution:

  ```
  python a_.py --show-resolution
  ```

- Ignore screen boundary checks:
  ```
  python a_.py X Y --ignore-bounds
  ```

## Using the Run Script

For convenience, you can use the provided run script which automatically handles the virtual environment:

```
./run.sh X Y [options]
```

Examples:

```
# Move the mouse
./run.sh 500 300

# Move and click
./run.sh 500 300 --left-click

# Move smoothly and right-click
./run.sh 500 300 --smooth --right-click

# Perform multiple clicks
./run.sh 500 300 --left-click --click-count 3 --click-interval 0.2

# Perform a drag operation
./run.sh 100 100 --drag-to-x 300 --drag-to-y 300

# Click, then drag, then click again
./run.sh 100 100 --drag-to-x 300 --drag-to-y 300 --click-before-drag --click-after-drag

# Double-click with right button, drag with right button, then right-click again
./run.sh 100 100 --drag-to-x 300 --drag-to-y 300 --click-before-drag --click-after-drag --double --right-click

# Monitor mouse position
./run.sh --monitor

# Keyboard examples with run.sh
./run.sh --key a
./run.sh --key enter
./run.sh --key c --modifiers ctrl
./run.sh --key delete --modifiers ctrl alt
./run.sh --key space --key-count 5 --key-interval 0.2
./run.sh --type "Hello, world!"

# Sequential action examples with run.sh
./run.sh 1298 993 --then-key a
./run.sh 500 300 --then-key enter --then-wait 1
./run.sh 800 600 --then-click left
./run.sh 1298 993 --then-key a --click-before-key left
./run.sh --do "move 1298 993; click left; key a"
./run.sh --do "move 500 300; wait 1; click right; key enter"
./run.sh --do "move 100 100; drag 300 300 --click-before --click-after"
./run.sh --do "move 500 300; click left; type \"Hello, world!\""
./run.sh --sequence '[{"type":"move","x":1298,"y":993},{"type":"key","key":"a"}]'
```

## Making the Script Executable (Linux/macOS)

You can make the script executable to run it directly:

```
chmod +x a_.py
./a_.py X Y [options]
```

## Requirements

- Python 3.6 or higher
- pynput 1.7.6
