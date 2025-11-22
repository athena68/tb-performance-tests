#!/bin/bash

# ThingsBoard Device Cleanup Script
# This script will delete all devices with EBMPAPST_FFU profile

echo "Starting device cleanup..."

# Login and get token
LOGIN_RESPONSE=$(curl -s -X POST "http://167.172.75.1:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "Failed to get authentication token"
  exit 1
fi

echo "Authentication successful"

# Get device profile ID for EBMPAPST_FFU
PROFILE_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/deviceProfiles?pageSize=100&page=0" \
  -H "X-Authorization: Bearer $TOKEN")

PROFILE_ID=$(echo $PROFILE_RESPONSE | jq -r '.data[] | select(.name=="EBMPAPST_FFU") | .id.id')

if [ -z "$PROFILE_ID" ] || [ "$PROFILE_ID" = "null" ]; then
  echo "EBMPAPST_FFU device profile not found"
  exit 1
fi

echo "Found EBMPAPST_FFU profile: $PROFILE_ID"

# Get all devices with EBMPAPST_FFU profile
DEVICES_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/devices?deviceProfileId=${PROFILE_ID}&pageSize=1000&page=0" \
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
    fi
  fi
done

echo "Device cleanup completed"