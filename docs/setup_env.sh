#!/bin/bash
# Setup script for Git Bash on Windows

# Set PYTHONPATH to current directory
export PYTHONPATH="$(pwd)"

echo "✓ PYTHONPATH set to: $PYTHONPATH"
echo ""
echo "You can now run:"
echo "  python main.py analyze YOUR_USERNAME"
echo "  python scripts/verify/verify_setup.py"
echo ""
