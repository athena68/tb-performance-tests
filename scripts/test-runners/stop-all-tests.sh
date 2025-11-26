#!/bin/bash
#
# Copyright © 2016-2025 The Thingsboard Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# Stop all background performance tests
#

echo "=========================================="
echo "Stopping All Performance Tests"
echo "=========================================="
echo ""

# Kill Java processes running PerformanceTestApplication
echo "Stopping Java performance test processes..."
pkill -f "PerformanceTestApplication" 2>/dev/null && echo "  ✓ Killed PerformanceTestApplication processes" || echo "  ℹ No PerformanceTestApplication processes found"

# Kill Maven spring-boot:run processes
echo "Stopping Maven spring-boot processes..."
pkill -f "spring-boot:run" 2>/dev/null && echo "  ✓ Killed spring-boot:run processes" || echo "  ℹ No spring-boot:run processes found"

# Kill any run-test-noninteractive.sh processes
echo "Stopping test runner scripts..."
pkill -f "run-test-noninteractive.sh" 2>/dev/null && echo "  ✓ Killed test runner scripts" || echo "  ℹ No test runner scripts found"

# Kill any start-ebmpapst-gateway.sh processes
echo "Stopping gateway test scripts..."
pkill -f "start-ebmpapst-gateway.sh" 2>/dev/null && echo "  ✓ Killed gateway test scripts" || echo "  ℹ No gateway test scripts found"

# Wait a moment for processes to terminate
sleep 2

# Check if any processes are still running
echo ""
echo "Checking for remaining processes..."
REMAINING=$(ps aux | grep -E "(PerformanceTest|spring-boot:run|run-test-noninteractive|start-ebmpapst-gateway)" | grep -v grep | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    echo "✓ All performance test processes stopped successfully!"
else
    echo "⚠ Warning: $REMAINING process(es) still running"
    echo ""
    echo "Remaining processes:"
    ps aux | grep -E "(PerformanceTest|spring-boot:run|run-test-noninteractive|start-ebmpapst-gateway)" | grep -v grep
    echo ""
    echo "To force kill all Java processes (use with caution):"
    echo "  pkill -9 java"
fi

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
