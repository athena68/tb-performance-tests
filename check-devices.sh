#!/bin/bash

echo "Checking ThingsBoard devices and profiles..."

# Login and get token
LOGIN_RESPONSE=$(curl -s -X POST "http://167.172.75.1:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token')

echo "Authentication token: $TOKEN"

# Check device profiles
echo "=== Device Profiles ==="
PROFILES_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/deviceProfiles?pageSize=100&page=0" \
  -H "X-Authorization: Bearer $TOKEN")
echo $PROFILES_RESPONSE | jq '.data[] | {id: .id.id, name: .name}'

# Check first 20 devices
echo "=== First 20 Devices ==="
DEVICES_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/devices?pageSize=20&page=0" \
  -H "X-Authorization: Bearer $TOKEN")
echo $DEVICES_RESPONSE | jq '.data[] | {id: .id.id, name: .name, profile: .deviceProfileName}'

# Check total device count
echo "=== Total Device Count ==="
echo $DEVICES_RESPONSE | jq '.totalElements'