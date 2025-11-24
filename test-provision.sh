#!/bin/bash
echo "=== Provision Script Test ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python3 --version)"
echo ""
echo "Starting provision script with 120 second timeout..."
echo ""

timeout 120 python3 -u test-scenarios/provision-scenario.py test-scenarios/scenario-hanoi-cleanroom.json 2>&1

EXIT_CODE=$?

echo ""
echo "=== Test Complete ==="
echo "Exit code: $EXIT_CODE"

if [ $EXIT_CODE -eq 124 ]; then
    echo "❌ Script TIMED OUT after 120 seconds (hanging detected)"
elif [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Script completed successfully"
else
    echo "⚠ Script exited with code: $EXIT_CODE"
fi
