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
