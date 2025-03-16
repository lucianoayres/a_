#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Setting up now..."
    ./setup_venv.sh
else
    # Activate the virtual environment
    source venv/bin/activate
fi

# Run the script with all arguments passed to this script
python a_.py "$@"

# Deactivate the virtual environment
deactivate