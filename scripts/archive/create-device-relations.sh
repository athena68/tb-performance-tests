#!/bin/bash
#
# Copyright © 2016-2025 The Thingsboard Authors
#
# Link FFU Devices to Cleanroom Assets for Option B Dashboard
# Links: Room R501 → DW00000000-DW00000029 (30 FFUs)
#        Room R502 → DW00000030-DW00000059 (30 FFUs)
#

echo "==========================================="
echo "Device Relations Setup (Option B)"
echo "==========================================="
echo ""

# Load configuration
if [ -f .env.ebmpapst-gateway ]; then
    export $(cat .env.ebmpapst-gateway | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
fi

REST_URL=${REST_URL:-http://167.99.64.71:8080}
REST_USERNAME=${REST_USERNAME:-tenant@thingsboard.org}
REST_PASSWORD=${REST_PASSWORD:-tenant}

echo "Configuration:"
echo "  Server: $REST_URL"
echo "  Username: $REST_USERNAME"
echo ""

# Check if asset IDs exist
if [ ! -f /tmp/cleanroom_assets.env ]; then
    echo "ERROR: /tmp/cleanroom_assets.env not found"
    echo "Please run ./create-cleanroom-assets.sh first"
    exit 1
fi

# Load asset IDs
source /tmp/cleanroom_assets.env

echo "Loaded Asset IDs:"
echo "  Room R501: $ROOM501_ID"
echo "  Room R502: $ROOM502_ID"
echo ""

# Check jq
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq is not installed"
    exit 1
fi

# Login
echo "Step 1: Logging in..."
TOKEN=$(curl -s -X POST "$REST_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" \
    | jq -r '.token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "✗ Login failed"
    exit 1
fi
echo "✓ Logged in"
echo ""

# Function to get device ID by name
get_device_id() {
    local device_name=$1
    local device_id=$(curl -s -X GET "$REST_URL/api/tenant/devices?deviceName=$device_name" \
        -H "X-Authorization: Bearer $TOKEN" \
        | jq -r '.id.id')
    echo "$device_id"
}

# Function to create relation
create_relation() {
    local from_id=$1
    local to_id=$2
    local device_name=$3

    local relation_json=$(cat <<EOF
{
  "from": {
    "entityType": "ASSET",
    "id": "$from_id"

  "to": {
    "entityType": "DEVICE",
    "id": "$to_id"

  "type": "Contains",
  "typeGroup": "COMMON"
}
EOF
)

    curl -s -X POST "$REST_URL/api/relation" \
        -H "Content-Type: application/json" \
        -H "X-Authorization: Bearer $TOKEN" \
        -d "$relation_json" > /dev/null

    echo "  ✓ $device_name → Room"
}

# Link devices to Room R501 (DW00000000-DW00000029)
echo "Step 2: Linking 30 FFUs to Room R501..."
success_count=0
for i in $(seq -w 0 29); do
    device_name="DW000000$i"
    device_id=$(get_device_id "$device_name")

    if [ -z "$device_id" ] || [ "$device_id" = "null" ]; then
        echo "  ✗ Device $device_name not found"
        continue
    fi

    create_relation "$ROOM501_ID" "$device_id" "$device_name"
    ((success_count++))
done
echo "✓ Linked $success_count devices to Room R501"
echo ""

# Link devices to Room R502 (DW00000030-DW00000059)
echo "Step 3: Linking 30 FFUs to Room R502..."
success_count=0
for i in $(seq -w 30 59); do
    device_name="DW000000$i"
    device_id=$(get_device_id "$device_name")

    if [ -z "$device_id" ] || [ "$device_id" = "null" ]; then
        echo "  ✗ Device $device_name not found"
        continue
    fi

    create_relation "$ROOM502_ID" "$device_id" "$device_name"
    ((success_count++))
done
echo "✓ Linked $success_count devices to Room R502"
echo ""

echo "==========================================="
echo "Device Relations Created Successfully!"
echo "==========================================="
echo ""
echo "Complete Hierarchy:"
echo "  Building A"
echo "  └─ Floor 5"
echo "      ├─ Room R501 (ISO 5)"
echo "      │   └─ 30 FFUs (DW00000000-DW00000029)"
echo "      └─ Room R502 (ISO 6)"
echo "          └─ 30 FFUs (DW00000030-DW00000059)"
echo ""
echo "Next step: Create hierarchical dashboard JSON"
echo "==========================================="
