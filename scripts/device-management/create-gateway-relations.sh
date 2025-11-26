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


# Script to create "Created" relations between gateways and devices
# This script creates the bidirectional "Created" relations required for gateway dashboards

set -e

# Configuration from .env.ebmpapst-gateway
REST_URL="${REST_URL:-}"
REST_USERNAME="${REST_USERNAME:-}"
REST_PASSWORD="${REST_PASSWORD:-}"

# Device and gateway configuration
GATEWAY_START_IDX=0
GATEWAY_END_IDX=2
DEVICE_START_IDX=0
DEVICE_END_IDX=60

echo "========================================="
echo "Gateway-Device Relation Creator"
echo "========================================="

# Validate required environment variables
if [ -z "$REST_URL" ] || [ -z "$REST_USERNAME" ] || [ -z "$REST_PASSWORD" ]; then
    echo "ERROR: Missing required environment variables:"
    echo "  - REST_URL: $REST_URL"
    echo "  - REST_USERNAME: $REST_USERNAME"
    echo "  - REST_PASSWORD: [${#REST_PASSWORD} chars]"
    echo ""
    echo "Please set these environment variables or source a .env file"
    exit 1
fi

echo "REST URL: $REST_URL"
echo "Username: $REST_USERNAME"
echo "Gateways: $GATEWAY_START_IDX to $GATEWAY_END_IDX"
echo "Devices: $DEVICE_START_IDX to $DEVICE_END_IDX"
echo "========================================="
echo ""

# Login and get token
echo "[1/4] Authenticating with ThingsBoard..."
TOKEN=$(curl -s -X POST "${REST_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" \
  | jq -r '.token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "ERROR: Failed to authenticate"
    exit 1
fi

echo "✓ Authentication successful"
echo ""

# Function to get device ID by name
get_device_id() {
    local device_name=$1
    curl -s -X GET "${REST_URL}/api/tenant/devices?deviceName=${device_name}" \
      -H "X-Authorization: Bearer $TOKEN" \
      | jq -r '.id.id // empty'
}

# Function to create relation
create_relation() {
    local from_id=$1
    local to_id=$2
    local relation_type=$3

    curl -s -X POST "${REST_URL}/api/relation" \
      -H "X-Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"from\": {
          \"entityType\": \"DEVICE\",
          \"id\": \"$from_id\"
      
        \"to\": {
          \"entityType\": \"DEVICE\",
          \"id\": \"$to_id\"
      
        \"type\": \"$relation_type\",
        \"typeGroup\": \"COMMON\"
      }" > /dev/null
}

# Calculate devices per gateway
total_gateways=$((GATEWAY_END_IDX - GATEWAY_START_IDX))
total_devices=$((DEVICE_END_IDX - DEVICE_START_IDX))
devices_per_gateway=$((total_devices / total_gateways))

echo "[2/4] Fetching gateway IDs..."

# Get gateway IDs
declare -A gateway_ids
for ((gw_idx=GATEWAY_START_IDX; gw_idx<GATEWAY_END_IDX; gw_idx++)); do
    gw_name=$(printf "GW%08d" $gw_idx)
    gw_id=$(get_device_id "$gw_name")

    if [ -z "$gw_id" ]; then
        echo "ERROR: Gateway $gw_name not found"
        exit 1
    fi

    gateway_ids[$gw_idx]=$gw_id
    echo "  ✓ $gw_name: $gw_id"
done

echo ""
echo "[3/4] Mapping devices to gateways..."

# Map devices to gateways based on scenario configuration
# GW00000000 -> DW00000000 to DW00000029 (30 devices)
# GW00000001 -> DW00000030 to DW00000059 (30 devices)

declare -A device_gateway_map

for ((dev_idx=DEVICE_START_IDX; dev_idx<DEVICE_END_IDX; dev_idx++)); do
    # Calculate which gateway this device belongs to (sequential blocks)
    gw_idx=$((dev_idx / devices_per_gateway + GATEWAY_START_IDX))

    # Ensure we don't exceed gateway range
    if [ $gw_idx -ge $GATEWAY_END_IDX ]; then
        gw_idx=$((GATEWAY_END_IDX - 1))
    fi

    device_gateway_map[$dev_idx]=$gw_idx
done

echo "✓ Device-gateway mapping complete"
echo "  Each gateway will manage $devices_per_gateway devices"
echo ""

echo "[4/4] Creating 'Created' relations..."

total_relations=0
successful_relations=0
failed_relations=0

for ((dev_idx=DEVICE_START_IDX; dev_idx<DEVICE_END_IDX; dev_idx++)); do
    dev_name=$(printf "DW%08d" $dev_idx)
    gw_idx=${device_gateway_map[$dev_idx]}
    gw_name=$(printf "GW%08d" $gw_idx)
    gw_id=${gateway_ids[$gw_idx]}

    # Get device ID
    dev_id=$(get_device_id "$dev_name")

    if [ -z "$dev_id" ]; then
        echo "  ✗ Device $dev_name not found (skipping)"
        ((failed_relations++))
        continue
    fi

    # Create bidirectional "Created" relations
    # 1. Gateway -> Device (From gateway)
    create_relation "$gw_id" "$dev_id" "Created"

    # 2. Device -> Gateway (From device, appears as "To" in device relations)
    create_relation "$dev_id" "$gw_id" "Created"

    ((total_relations += 2))
    ((successful_relations += 2))

    # Progress indicator
    if [ $((dev_idx % 10)) -eq 0 ]; then
        echo "  ✓ Progress: $dev_idx/$total_devices devices processed..."
    fi
done

echo ""
echo "========================================="
echo "Relation Creation Summary"
echo "========================================="
echo "Total relations created: $successful_relations"
echo "Failed relations: $failed_relations"
echo "Gateways processed: $total_gateways"
echo "Devices processed: $total_devices"
echo "========================================="
echo ""

echo "Verification:"
echo "  1. Login to ThingsBoard UI: $REST_URL"
echo "  2. Navigate to: Devices → GW00000000 → Relations"
echo "  3. You should see 'Created' relations to all devices"
echo ""
echo "Done!"
