#!/bin/bash

# update documentation from submodule
echo "Updating documentation..."
git submodule update --remote nersc-docs

# activate the environment
source venv/bin/activate

# run the search tool
python search.py