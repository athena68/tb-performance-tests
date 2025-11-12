#!/bin/bash
#
# Copyright © 2016-2025 The Thingsboard Authors
#
# Setup gateway credentials - Sets each gateway's access token to match its name
# This is required for the performance test to work correctly
#

echo "=========================================="
echo "Gateway Credentials Setup"
echo "=========================================="
echo ""

# Load configuration
if [ -f .env.ebmpapst-gateway ]; then
    export $(cat .env.ebmpapst-gateway | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
else
    echo "ERROR: .env.ebmpapst-gateway not found!"
    exit 1
fi

echo "Configuration:"
echo "  Server: $REST_URL"
echo "  Username: $REST_USERNAME"
echo ""

# Login to ThingsBoard
echo "Logging in to ThingsBoard..."
TOKEN=$(curl -s -X POST "$REST_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" \
    | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "ERROR: Failed to login to ThingsBoard"
    exit 1
fi

echo "✓ Logged in successfully"
echo ""

# Process each gateway
NUM_GATEWAYS=$((GATEWAY_END_IDX - GATEWAY_START_IDX + 1))
echo "Setting up credentials for $NUM_GATEWAYS gateway(s)..."
echo ""

SUCCESS_COUNT=0
FAILED_COUNT=0

for i in $(seq $GATEWAY_START_IDX $GATEWAY_END_IDX); do
    GW_NAME="GW$(printf '%08d' $i)"

    # Find gateway device
    echo "Processing: $GW_NAME"

    DEVICE_INFO=$(curl -s -X GET "$REST_URL/api/tenant/devices?pageSize=1000&page=0" \
        -H "X-Authorization: Bearer $TOKEN")

    # Use jq if available, otherwise fallback to grep
    if command -v jq &> /dev/null; then
        DEVICE_ID=$(echo "$DEVICE_INFO" | jq -r ".data[] | select(.name==\"$GW_NAME\") | .id.id" 2>/dev/null)
    else
        DEVICE_ID=$(echo "$DEVICE_INFO" | grep -o "\"name\":\"$GW_NAME\"" -B 50 | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
    fi

    if [ -z "$DEVICE_ID" ] || [ "$DEVICE_ID" = "null" ]; then
        echo "  ✗ Gateway device not found"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        continue
    fi

    # Get current credentials
    CREDS=$(curl -s -X GET "$REST_URL/api/device/$DEVICE_ID/credentials" \
        -H "X-Authorization: Bearer $TOKEN")

    # Update credentials - set token to gateway name
    UPDATED_CREDS=$(echo "$CREDS" | sed "s/\"credentialsId\":\"[^\"]*\"/\"credentialsId\":\"$GW_NAME\"/")

    RESULT=$(curl -s -X POST "$REST_URL/api/device/credentials" \
        -H "X-Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$UPDATED_CREDS")

    if echo "$RESULT" | grep -q "\"id\""; then
        echo "  ✓ Access token set to: $GW_NAME"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "  ✗ Failed to update credentials"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
done

echo ""
echo "=========================================="
echo "Setup Summary:"
echo "=========================================="
echo "  Successful: $SUCCESS_COUNT"
echo "  Failed: $FAILED_COUNT"
echo ""

if [ $FAILED_COUNT -eq 0 ]; then
    echo "✓ All gateway credentials configured successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./start-ebmpapst-gateway.sh"
    echo "  2. The test will use gateways: GW$(printf '%08d' $GATEWAY_START_IDX) to GW$(printf '%08d' $GATEWAY_END_IDX)"
else
    echo "⚠ Some gateways failed to configure"
    echo "Please check the gateways manually in ThingsBoard UI"
fi

echo ""
