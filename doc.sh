#!/bin/bash

# Check for debug flag
DEBUG_FLAG=""
if [[ "$1" == "-debug" ]]; then
    DEBUG_FLAG="-debug"
    echo "🐛 DEBUG MODE: Tool call thinking and I/O will be displayed"
fi

# update documentation from submodule
echo "Updating documentation..."
git submodule update --remote nersc-docs

# activate the environment
source venv/bin/activate

# run the search tool with optional debug flag
python search.py $DEBUG_FLAG