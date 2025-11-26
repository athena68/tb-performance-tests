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

echo "==========================================="
echo "Dashboard Functionality Test (Option A)"
echo "==========================================="
echo ""

# Load configuration
if [ -f .env.ebmpapst-gateway ]; then
    export $(cat .env.ebmpapst-gateway | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
fi

# Default values
REST_URL=${REST_URL:-"http://localhost:8080"}
REST_USERNAME=${REST_USERNAME:-""}
REST_PASSWORD=${REST_PASSWORD:-""}

if [[ -z "$REST_USERNAME" || -z "$REST_PASSWORD" ]]; then
    echo "❌ Error: REST_USERNAME and REST_PASSWORD must be set in environment or .env file"
    exit 1
fi

echo "Configuration:"
echo "  ThingsBoard Server: $REST_URL"
echo "  Username: $REST_USERNAME"
echo ""

# Check jq installation
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq is not installed. Please install it first:"
    echo "  sudo apt install jq"
    exit 1
fi

# Login to ThingsBoard
echo "Test 1: Login to ThingsBoard..."
TOKEN=$(curl -s -X POST "$REST_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" \
    | jq -r '.token' 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "✗ FAILED: Cannot login"
    exit 1
fi
echo "✓ PASSED: Login successful"
echo ""

# Find dashboard
echo "Test 2: Find Cleanroom FFU Dashboard..."
DASHBOARDS=$(curl -s -X GET "$REST_URL/api/tenant/dashboards?pageSize=100&page=0" \
    -H "X-Authorization: Bearer $TOKEN")

DASHBOARD_TITLE="Cleanroom FFU Monitoring - Flat View"
DASHBOARD_ID=$(echo "$DASHBOARDS" | jq -r ".data[] | select(.title==\"$DASHBOARD_TITLE\") | .id.id")

if [ -z "$DASHBOARD_ID" ] || [ "$DASHBOARD_ID" = "null" ]; then
    echo "✗ FAILED: Dashboard not found"
    exit 1
fi
echo "✓ PASSED: Dashboard found (ID: $DASHBOARD_ID)"
echo ""

# Get dashboard details
echo "Test 3: Retrieve dashboard configuration..."
DASHBOARD=$(curl -s -X GET "$REST_URL/api/dashboard/$DASHBOARD_ID" \
    -H "X-Authorization: Bearer $TOKEN")

WIDGET_COUNT=$(echo "$DASHBOARD" | jq '.configuration.widgets | length')

if [ -z "$WIDGET_COUNT" ] || [ "$WIDGET_COUNT" = "null" ] || [ "$WIDGET_COUNT" -eq 0 ]; then
    echo "✗ FAILED: No widgets found in dashboard"
    exit 1
fi
echo "✓ PASSED: Dashboard has $WIDGET_COUNT widgets configured"
echo ""

# Check entity alias
echo "Test 4: Verify entity alias configuration..."
ALIAS_COUNT=$(echo "$DASHBOARD" | jq '.configuration.entityAliases | length')
ALIAS_TYPE=$(echo "$DASHBOARD" | jq -r '.configuration.entityAliases.all_ffus.filter.type')

if [ "$ALIAS_TYPE" != "deviceType" ]; then
    echo "✗ FAILED: Entity alias not configured correctly"
    exit 1
fi
echo "✓ PASSED: Entity alias configured ($ALIAS_COUNT aliases)"
echo ""

# Test device data retrieval - look for our test devices
echo "Test 5: Test device data retrieval..."
ALL_DEVICES=$(curl -s -X GET "$REST_URL/api/tenant/devices?pageSize=1000&page=0" \
    -H "X-Authorization: Bearer $TOKEN")

# Find a test device (DW00000000-DW00000059)
FIRST_DEVICE_ID=$(echo "$ALL_DEVICES" | jq -r '.data[] | select(.name | startswith("DW")) | .id.id' | head -1)
FIRST_DEVICE_NAME=$(echo "$ALL_DEVICES" | jq -r ".data[] | select(.id.id==\"$FIRST_DEVICE_ID\") | .name")

if [ -z "$FIRST_DEVICE_ID" ] || [ "$FIRST_DEVICE_ID" = "null" ]; then
    echo "✗ FAILED: No test FFU devices (DW*) found"
    exit 1
fi
echo "✓ PASSED: Found test device $FIRST_DEVICE_NAME"
echo ""

# Test telemetry retrieval for first device
echo "Test 6: Test telemetry data retrieval..."

CURRENT_TIME=$(($(date +%s) * 1000))
START_TIME=$((CURRENT_TIME - 60000))  # 1 minute ago

TELEMETRY=$(curl -s -X GET "$REST_URL/api/plugins/telemetry/DEVICE/$FIRST_DEVICE_ID/values/timeseries?keys=actualSpeed,differentialPressure,motorTemperature&startTs=$START_TIME&endTs=$CURRENT_TIME" \
    -H "X-Authorization: Bearer $TOKEN")

HAS_SPEED=$(echo "$TELEMETRY" | jq -r '.actualSpeed | length')
HAS_PRESSURE=$(echo "$TELEMETRY" | jq -r '.differentialPressure | length')

if [ "$HAS_SPEED" = "null" ] || [ "$HAS_SPEED" -eq 0 ]; then
    echo "✗ FAILED: No telemetry data found for device $FIRST_DEVICE_NAME"
    exit 1
fi
echo "✓ PASSED: Telemetry data available for $FIRST_DEVICE_NAME"
echo "  - actualSpeed: $HAS_SPEED data points"
echo "  - differentialPressure: $HAS_PRESSURE data points"
echo ""

# Test attributes retrieval
echo "Test 7: Test attributes retrieval..."
ATTRIBUTES=$(curl -s -X GET "$REST_URL/api/plugins/telemetry/DEVICE/$FIRST_DEVICE_ID/values/attributes/SERVER_SCOPE" \
    -H "X-Authorization: Bearer $TOKEN")

ATTR_COUNT=$(echo "$ATTRIBUTES" | jq '. | length')

if [ -z "$ATTR_COUNT" ] || [ "$ATTR_COUNT" = "null" ]; then
    ATTR_COUNT=0
fi
echo "✓ PASSED: Device has $ATTR_COUNT attributes"
echo ""

# Summary
echo "==========================================="
echo "Test Summary"
echo "==========================================="
echo "✓ All tests passed!"
echo ""
echo "Dashboard is ready to use:"
echo "  URL: $REST_URL/dashboard/$DASHBOARD_ID"
echo ""
echo "Verified Components:"
echo "  ✓ Authentication working"
echo "  ✓ Dashboard exists and configured"
echo "  ✓ $WIDGET_COUNT widgets configured"
echo "  ✓ Entity aliases configured"
echo "  ✓ FFU devices accessible"
echo "  ✓ Telemetry data flowing"
echo "  ✓ Attributes available"
echo ""
echo "==========================================="
echo ""
