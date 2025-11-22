#!/bin/bash

echo "=== Deleting All Old Devices (Keeping only GW00000000 and DW00000000-DW00000004) ==="

# Get authentication token
LOGIN_RESPONSE=$(curl -s -X POST "http://167.172.75.1:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "Failed to get authentication token"
  exit 1
fi

echo "Authentication successful"
echo "Fetching all devices..."

# Devices to KEEP ( whitelist)
KEEP_DEVICES=("GW00000000" "DW00000000" "DW00000001" "DW00000002" "DW00000003" "DW00000004")

# Function to check if device should be kept
should_keep_device() {
    local device_name=$1
    for keep in "${KEEP_DEVICES[@]}"; do
        if [ "$device_name" = "$keep" ]; then
            return 0  # Keep this device
        fi
    done
    return 1  # Delete this device
}

# Get total device count
TOTAL_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/devices?pageSize=100&page=0" \
  -H "X-Authorization: Bearer $TOKEN")

TOTAL_DEVICES=$(echo $TOTAL_RESPONSE | jq '.totalElements')

if [ -z "$TOTAL_DEVICES" ] || [ "$TOTAL_DEVICES" = "null" ]; then
    TOTAL_DEVICES=0
fi

echo "Found $TOTAL_DEVICES total devices"
echo "Devices to keep: ${KEEP_DEVICES[*]}"
echo "Devices to delete: $((TOTAL_DEVICES - ${#KEEP_DEVICES[@]}))"

if [ "$TOTAL_DEVICES" -eq 0 ]; then
  echo "No devices to delete"
  exit 0
fi

if [ $((TOTAL_DEVICES - ${#KEEP_DEVICES[@]})) -eq 0 ]; then
  echo "Only devices to keep found. No deletion needed."
  exit 0
fi

# Delete devices page by page, but skip the ones we want to keep
PAGE_SIZE=100
PAGE=0
DELETED_COUNT=0
SKIPPED_COUNT=0

while true; do
  echo "Fetching devices on page $PAGE..."

  # Get devices for this page
  DEVICES_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/devices?pageSize=$PAGE_SIZE&page=$PAGE" \
    -H "X-Authorization: Bearer $TOKEN")

  DEVICE_COUNT=$(echo $DEVICES_RESPONSE | jq '.data | length')

  if [ "$DEVICE_COUNT" -eq 0 ]; then
    break
  fi

  echo "Found $DEVICE_COUNT devices on this page"

  # Check each device
  for i in $(seq 0 $((DEVICE_COUNT-1))); do
    DEVICE_ID=$(echo $DEVICES_RESPONSE | jq -r ".data[$i].id.id")
    DEVICE_NAME=$(echo $DEVICES_RESPONSE | jq -r ".data[$i].name")

    if should_keep_device "$DEVICE_NAME"; then
      echo "KEEPING device: $DEVICE_NAME (ID: $DEVICE_ID)"
      SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    else
      echo "DELETING device: $DEVICE_NAME (ID: $DEVICE_ID)"

      # Use correct endpoint: /api/device instead of /api/tenant/device
      DELETE_RESPONSE=$(curl -s -X DELETE "http://167.172.75.1:8080/api/device/$DEVICE_ID" \
        -H "X-Authorization: Bearer $TOKEN")

      DELETED_COUNT=$((DELETED_COUNT + 1))

      if [ $((DELETED_COUNT % 10)) -eq 0 ]; then
        echo "Deleted $DELETED_COUNT devices so far..."
      fi
    fi
  done

  PAGE=$((PAGE + 1))
done

echo ""
echo "=== DELETION SUMMARY ==="
echo "✓ Successfully deleted $DELETED_COUNT devices"
echo "✓ Kept $SKIPPED_COUNT devices (whitelisted)"
echo "✓ Total devices processed: $((DELETED_COUNT + SKIPPED_COUNT))"

# Verify final state
echo ""
echo "Verifying final device count..."

VERIFY_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/devices?pageSize=1&page=0" \
  -H "X-Authorization: Bearer $TOKEN")

FINAL_COUNT=$(echo $VERIFY_RESPONSE | jq '.totalElements')

echo "Final device count: $FINAL_COUNT"

if [ "$FINAL_COUNT" = "${#KEEP_DEVICES[@]}" ]; then
  echo "✅ SUCCESS: Only the ${#KEEP_DEVICES[@]} whitelisted devices remain"
else
  echo "⚠️  WARNING: Expected ${#KEEP_DEVICES[@]} devices but found $FINAL_COUNT"
fi

echo "Devices remaining should be: ${KEEP_DEVICES[*]}"