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
