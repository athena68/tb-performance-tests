#!/bin/bash

echo "Deleting ThingsBoard devices..."

# Login and get token
LOGIN_RESPONSE=$(curl -s -X POST "http://167.172.75.1:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token')

echo "Authentication successful"

# Get all devices (paginate through them)
PAGE_SIZE=100
PAGE=0
TOTAL_DELETED=0

while true; do
  echo "Fetching devices page $PAGE..."
  DEVICES_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/devices?pageSize=${PAGE_SIZE}&page=${PAGE}" \
    -H "X-Authorization: Bearer $TOKEN")

  # Extract device IDs and delete them
  echo $DEVICES_RESPONSE | jq -r '.data[].id.id' | while read DEVICE_ID; do
    if [ -n "$DEVICE_ID" ] && [ "$DEVICE_ID" != "null" ]; then
      echo "Deleting device: $DEVICE_ID"
      DELETE_RESPONSE=$(curl -s -X DELETE "http://167.172.75.1:8080/api/tenant/device/$DEVICE_ID" \
        -H "X-Authorization: Bearer $TOKEN")

      if echo "$DELETE_RESPONSE" | jq -e '.status' > /dev/null 2>&1; then
        echo "  Error deleting device: $(echo $DELETE_RESPONSE | jq -r '.message')"
      else
        echo "  Device deleted successfully"
        TOTAL_DELETED=$((TOTAL_DELETED + 1))
      fi
    fi
  done

  # Check if there are more pages
  TOTAL_ELEMENTS=$(echo $DEVICES_RESPONSE | jq -r '.totalElements // 0')
  HAS_NEXT=$(echo $DEVICES_RESPONSE | jq -r '.hasNext // false')

  if [ "$HAS_NEXT" = "false" ]; then
    break
  fi

  PAGE=$((PAGE + 1))
done

echo "Device deletion completed. Deleted $TOTAL_DELETED devices."