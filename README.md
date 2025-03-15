# a\_

A simple Python utility to move the mouse cursor to specified coordinates using command line arguments.

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

Basic usage (with virtual environment activated):

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

### Optional Arguments

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

### Screen Resolution Awareness

The script now detects your screen resolution and warns you if the coordinates are outside the screen boundaries. You can:

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
./run.sh X Y
```

This will:

1. Check if the virtual environment exists and create it if needed
2. Activate the virtual environment
3. Run the script with your arguments
4. Deactivate the virtual environment when done

## Making the Script Executable (Linux/macOS)

You can make the script executable to run it directly:

```
chmod +x a_.py
./a_.py X Y
```

## Requirements

- Python 3.6 or higher
- pynput 1.7.6
