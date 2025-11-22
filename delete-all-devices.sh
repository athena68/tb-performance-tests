#!/bin/bash

echo "=== Deleting All Existing Devices ==="

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

# Get total device count
TOTAL_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/devices?pageSize=100&page=0" \
  -H "X-Authorization: Bearer $TOKEN")

TOTAL_DEVICES=$(echo $TOTAL_RESPONSE | jq '.totalElements')

if [ -z "$TOTAL_DEVICES" ] || [ "$TOTAL_DEVICES" = "null" ]; then
  TOTAL_DEVICES=0
fi

echo "Found $TOTAL_DEVICES devices to delete"

if [ "$TOTAL_DEVICES" -eq 0 ]; then
  echo "No devices to delete"
  exit 0
fi

# Delete all devices page by page
PAGE_SIZE=100
PAGE=0
DELETED_COUNT=0

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

  # Delete each device
  for i in $(seq 0 $((DEVICE_COUNT-1))); do
    DEVICE_ID=$(echo $DEVICES_RESPONSE | jq -r ".data[$i].id.id")
    DEVICE_NAME=$(echo $DEVICES_RESPONSE | jq -r ".data[$i].name")

    echo "Deleting device: $DEVICE_NAME (ID: $DEVICE_ID)"

    DELETE_RESPONSE=$(curl -s -X DELETE "http://167.172.75.1:8080/api/tenant/device/$DEVICE_ID" \
      -H "X-Authorization: Bearer $TOKEN")

    DELETED_COUNT=$((DELETED_COUNT + 1))

    if [ $((DELETED_COUNT % 10)) -eq 0 ]; then
      echo "Deleted $DELETED_COUNT devices so far..."
    fi
  done

  PAGE=$((PAGE + 1))
done

echo ""
echo "✓ Successfully deleted $DELETED_COUNT devices"
echo "All devices have been removed from the server"