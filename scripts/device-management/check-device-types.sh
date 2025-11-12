#!/bin/bash

# Load configuration
if [ -f .env.ebmpapst-gateway ]; then
    export $(cat .env.ebmpapst-gateway | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
fi

REST_URL=${REST_URL:-"http://localhost:8080"}
REST_USERNAME=${REST_USERNAME:-""}
REST_PASSWORD=${REST_PASSWORD:-""}

if [[ -z "$REST_USERNAME" || -z "$REST_PASSWORD" ]]; then
    echo "❌ Error: REST_USERNAME and REST_PASSWORD must be set in environment or .env file"
    exit 1
fi

# Login
TOKEN=$(curl -s -X POST "$REST_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" \
    | jq -r '.token')

echo "Checking device types for DW devices..."
echo ""

# Get all devices
ALL_DEVICES=$(curl -s -X GET "$REST_URL/api/tenant/devices?pageSize=1000&page=0" \
    -H "X-Authorization: Bearer $TOKEN")

# Check first 5 DW devices
echo "Sample of DW devices:"
echo "$ALL_DEVICES" | jq -r '.data[] | select(.name | startswith("DW")) | "\(.name) - Type: \(.type)"' | head -5

echo ""
echo "Checking device type filter..."

# Test deviceType filter
FILTERED=$(curl -s -X GET "$REST_URL/api/tenant/devices?deviceType=EBMPAPST_FFU&pageSize=10&page=0" \
    -H "X-Authorization: Bearer $TOKEN")

COUNT=$(echo "$FILTERED" | jq '.data | length')

echo "Devices matching type 'EBMPAPST_FFU': $COUNT"

if [ "$COUNT" -eq 0 ]; then
    echo ""
    echo "No devices found with type EBMPAPST_FFU!"
    echo ""
    echo "Let's check what types exist:"
    echo "$ALL_DEVICES" | jq -r '.data[].type' | sort -u
fi
