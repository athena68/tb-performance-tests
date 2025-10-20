#!/bin/bash
#
# Copyright © 2016-2025 The Thingsboard Authors
#
# Verify ebmpapst FFU Test Setup on ThingsBoard
# This script checks that all devices, gateway, and data are operational
#

echo "=========================================="
echo "ebmpapst FFU Setup Verification"
echo "=========================================="
echo ""

# Load configuration
if [ -f .env.ebmpapst-gateway ]; then
    export $(cat .env.ebmpapst-gateway | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
fi

# Default values
REST_URL=${REST_URL:-http://167.99.64.71:8080}
REST_USERNAME=${REST_USERNAME:-tenant@thingsboard.org}
REST_PASSWORD=${REST_PASSWORD:-tenant}
DEVICE_START_IDX=${DEVICE_START_IDX:-0}
DEVICE_END_IDX=${DEVICE_END_IDX:-60}

echo "Configuration:"
echo "  ThingsBoard Server: $REST_URL"
echo "  Username: $REST_USERNAME"
echo "  Device Range: DW$(printf '%08d' $DEVICE_START_IDX) - DW$(printf '%08d' $((DEVICE_END_IDX - 1)))"
echo ""

# Check jq installation
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq is not installed. Please install it first:"
    echo "  sudo apt install jq"
    exit 1
fi

# Login to ThingsBoard
echo "Step 1: Logging in to ThingsBoard..."
TOKEN=$(curl -s -X POST "$REST_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" \
    | jq -r '.token' 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "✗ ERROR: Failed to login to ThingsBoard"
    exit 1
fi
echo "✓ Logged in successfully"
echo ""

# Check gateway exists
echo "Step 2: Checking gateway GW00000000..."
ALL_DEVICES=$(curl -s -X GET "$REST_URL/api/tenant/devices?pageSize=1000&page=0" \
    -H "X-Authorization: Bearer $TOKEN")

GATEWAY_ID=$(echo "$ALL_DEVICES" | jq -r '.data[] | select(.name=="GW00000000") | .id.id')

if [ -z "$GATEWAY_ID" ] || [ "$GATEWAY_ID" = "null" ]; then
    echo "✗ WARNING: Gateway GW00000000 not found"
    GATEWAY_EXISTS=false
else
    echo "✓ Gateway GW00000000 exists (ID: $GATEWAY_ID)"
    GATEWAY_EXISTS=true
fi
echo ""

# Check device profile
echo "Step 3: Checking device profile EBMPAPST_FFU..."
DEVICE_PROFILES=$(curl -s -X GET "$REST_URL/api/deviceProfiles?pageSize=100&page=0" \
    -H "X-Authorization: Bearer $TOKEN")

PROFILE_ID=$(echo "$DEVICE_PROFILES" | jq -r '.data[] | select(.name=="EBMPAPST_FFU") | .id.id')

if [ -z "$PROFILE_ID" ] || [ "$PROFILE_ID" = "null" ]; then
    echo "✗ WARNING: Device profile EBMPAPST_FFU not found"
else
    echo "✓ Device profile EBMPAPST_FFU exists (ID: $PROFILE_ID)"
fi
echo ""

# Check FFU devices
echo "Step 4: Checking FFU devices..."
FOUND_DEVICES=0
MISSING_DEVICES=0
DEVICES_WITH_TELEMETRY=0
MISSING_LIST=""

for i in $(seq $DEVICE_START_IDX $((DEVICE_END_IDX - 1))); do
    DEVICE_NAME="DW$(printf '%08d' $i)"

    DEVICE_ID=$(echo "$ALL_DEVICES" | jq -r ".data[] | select(.name==\"$DEVICE_NAME\") | .id.id")

    if [ -z "$DEVICE_ID" ] || [ "$DEVICE_ID" = "null" ]; then
        MISSING_DEVICES=$((MISSING_DEVICES + 1))
        MISSING_LIST="$MISSING_LIST\n  - $DEVICE_NAME"
    else
        FOUND_DEVICES=$((FOUND_DEVICES + 1))

        # Check if device has recent telemetry (last 5 minutes)
        CURRENT_TIME=$(($(date +%s) * 1000))
        START_TIME=$((CURRENT_TIME - 300000))  # 5 minutes ago

        TELEMETRY=$(curl -s -X GET "$REST_URL/api/plugins/telemetry/DEVICE/$DEVICE_ID/values/timeseries?keys=actualSpeed&startTs=$START_TIME&endTs=$CURRENT_TIME" \
            -H "X-Authorization: Bearer $TOKEN")

        HAS_DATA=$(echo "$TELEMETRY" | jq -r '.actualSpeed | length')

        if [ "$HAS_DATA" != "null" ] && [ "$HAS_DATA" -gt 0 ]; then
            DEVICES_WITH_TELEMETRY=$((DEVICES_WITH_TELEMETRY + 1))
        fi
    fi

    # Progress indicator
    if [ $((i % 10)) -eq 0 ]; then
        echo "  Checked $(((i - DEVICE_START_IDX) + 1))/$((DEVICE_END_IDX - DEVICE_START_IDX)) devices..."
    fi
done

echo ""
echo "Device Status Summary:"
echo "  Total Expected: $((DEVICE_END_IDX - DEVICE_START_IDX)) devices"
echo "  Found: $FOUND_DEVICES devices"
echo "  Missing: $MISSING_DEVICES devices"
echo "  With Recent Telemetry: $DEVICES_WITH_TELEMETRY devices"

if [ $MISSING_DEVICES -gt 0 ]; then
    echo ""
    echo "Missing Devices:$MISSING_LIST"
fi
echo ""

# Check gateway relations (if gateway exists)
if [ "$GATEWAY_EXISTS" = true ]; then
    echo "Step 5: Checking gateway relations..."

    RELATIONS=$(curl -s -X GET "$REST_URL/api/relations?fromId=$GATEWAY_ID&fromType=DEVICE" \
        -H "X-Authorization: Bearer $TOKEN")

    RELATION_COUNT=$(echo "$RELATIONS" | jq '. | length')

    if [ "$RELATION_COUNT" = "null" ]; then
        RELATION_COUNT=0
    fi

    echo "  Gateway has $RELATION_COUNT device relations"

    if [ $RELATION_COUNT -eq 0 ]; then
        echo "✗ WARNING: Gateway has no device relations"
        echo "  This means devices were not provisioned via gateway connect API"
        echo "  Recommendation: Set DEVICE_CREATE_ON_START=false and restart test"
    else
        echo "✓ Gateway has device relations established"
    fi
    echo ""
fi

# Final summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="

ISSUES=0

if [ "$GATEWAY_EXISTS" = false ]; then
    echo "✗ Gateway GW00000000 not found"
    ISSUES=$((ISSUES + 1))
else
    echo "✓ Gateway exists"
fi

if [ -z "$PROFILE_ID" ] || [ "$PROFILE_ID" = "null" ]; then
    echo "✗ Device profile EBMPAPST_FFU not found"
    ISSUES=$((ISSUES + 1))
else
    echo "✓ Device profile exists"
fi

if [ $FOUND_DEVICES -lt $((DEVICE_END_IDX - DEVICE_START_IDX)) ]; then
    echo "✗ Missing $MISSING_DEVICES devices"
    ISSUES=$((ISSUES + 1))
else
    echo "✓ All $FOUND_DEVICES devices exist"
fi

if [ $DEVICES_WITH_TELEMETRY -lt $((FOUND_DEVICES / 2)) ]; then
    echo "✗ Only $DEVICES_WITH_TELEMETRY devices have recent telemetry"
    echo "  Expected at least $((FOUND_DEVICES / 2)) devices with active data"
    ISSUES=$((ISSUES + 1))
else
    echo "✓ $DEVICES_WITH_TELEMETRY devices sending telemetry"
fi

echo ""

if [ $ISSUES -eq 0 ]; then
    echo "=========================================="
    echo "✓ ALL CHECKS PASSED!"
    echo "=========================================="
    echo ""
    echo "Your setup is ready for dashboard creation."
    echo ""
    exit 0
else
    echo "=========================================="
    echo "✗ FOUND $ISSUES ISSUES"
    echo "=========================================="
    echo ""
    echo "Please fix the issues above before creating dashboard."
    echo ""
    echo "If devices are missing, run:"
    echo "  ./start-ebmpapst-gateway.sh"
    echo ""
    exit 1
fi
