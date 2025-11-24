#!/bin/bash
#
# Copyright © 2016-2025 The Thingsboard Authors
#
# ebmpapst FFU Performance Test - Gateway Mode
# Uses an EXISTING gateway to communicate with ThingsBoard
#

echo "=========================================="
echo "ebmpapst FFU Gateway Mode Test"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env]; then
    echo "ERROR: .env not found!"
    echo ""
    echo "Please create .env"
    exit 1
fi

# Load environment variables
echo "Loading configuration from .env..."
export $(cat .env | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
echo "Configuration loaded!"
echo ""

echo "=========================================="
echo "IMPORTANT PRE-REQUISITES:"
echo "=========================================="
echo ""
echo "✓ Your gateways must be connected to ThingsBoard"
echo "✓ Gateway access tokens must match their device names:"
echo ""

# Calculate number of gateways (END_IDX is exclusive like Python range)
NUM_GATEWAYS=$((GATEWAY_END_IDX - GATEWAY_START_IDX))
echo "  This test requires $NUM_GATEWAYS gateway(s):"
for i in $(seq $GATEWAY_START_IDX $((GATEWAY_END_IDX - 1))); do
    GW_NAME="GW$(printf '%08d' $i)"
    echo "    - Gateway: $GW_NAME → Token: $GW_NAME"
done

echo ""
echo "To change gateway tokens:"
echo "1. Go to: $REST_URL"
echo "2. Devices → Your Gateway → Manage credentials"
echo "3. Change access token to match gateway name (e.g., GW00000000)"
echo "4. Save and reconnect your gateway"
echo ""

read -p "Are all gateway tokens configured and connected? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please configure all gateway tokens first, then run this script again."
    exit 1
fi

echo ""
echo "Test Configuration:"
echo "  Mode: GATEWAY (TEST_API=gateway)"
echo "  ThingsBoard Server: $REST_URL"
echo "  MQTT Broker: $MQTT_HOST:${MQTT_PORT:-1883}"
echo "  Number of Gateways: $NUM_GATEWAYS (GW$(printf '%08d' $GATEWAY_START_IDX) to GW$(printf '%08d' $((GATEWAY_END_IDX - 1))))"
echo "  Number of FFU Devices: $((DEVICE_END_IDX - DEVICE_START_IDX))"
echo "  Create Devices: $DEVICE_CREATE_ON_START"
echo "  Messages per Second: $MESSAGES_PER_SECOND"
echo "  Test Duration: $DURATION_IN_SECONDS seconds"
echo ""

read -p "Start gateway test? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Test cancelled."
    exit 1
fi

echo ""
echo "Starting ebmpapst FFU Gateway Performance Test..."
echo ""

mvn spring-boot:run

echo ""
echo "=========================================="
echo "Test completed!"
echo "=========================================="
echo ""
echo "Verify on ThingsBoard UI:"
echo "1. Go to Devices → Filter by 'GW'"
echo "2. For each gateway (GW00000000, GW00000001, etc.):"
echo "   - Check 'Relations' tab → Should see connected FFU devices"
echo "3. Click any FFU device → Latest telemetry"
echo "4. You should see ebmpapst FFU telemetry data"
echo ""
echo "Gateway distribution:"
for i in $(seq $GATEWAY_START_IDX $((GATEWAY_END_IDX - 1))); do
    GW_NAME="GW$(printf '%08d' $i)"
    echo "  - $GW_NAME: Check its device relations"
done
