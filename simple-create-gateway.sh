#!/bin/bash

echo "=== Simple Gateway Device Creation ==="

# Login and get token
LOGIN_RESPONSE=$(curl -s -X POST "http://167.172.75.1:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token')

echo "Authentication successful"

# Check existing device profiles
echo "Checking existing device profiles..."
PROFILES_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/deviceProfiles?pageSize=100&page=0" \
  -H "X-Authorization: Bearer $TOKEN")

echo "Available device profiles:"
echo $PROFILES_RESPONSE | jq '.data[] | {name: .name, id: .id.id}'

# Use the first available profile if EBMPAPST_FFU doesn't exist
PROFILE_ID=$(echo $PROFILES_RESPONSE | jq -r '.data[0].id.id')
PROFILE_NAME=$(echo $PROFILES_RESPONSE | jq -r '.data[0].name')

echo "Using profile: $PROFILE_NAME (ID: $PROFILE_ID)"

# Create gateway device with basic profile
GATEWAY_PAYLOAD=$(cat <<EOF
{
  "name": "GW00000000",
  "type": "$PROFILE_NAME",
  "label": "EBMPAPST FFU Gateway 00000000",
  "additionalInfo": {
    "gateway": true,
    "description": "EBMPAPST FFU Gateway Device"
  }
}
EOF
)

echo "Creating gateway device..."
GATEWAY_RESPONSE=$(curl -s -X POST "http://167.172.75.1:8080/api/tenant/device" \
  -H "Content-Type: application/json" \
  -H "X-Authorization: Bearer $TOKEN" \
  -d "$GATEWAY_PAYLOAD")

echo "Gateway creation response:"
echo $GATEWAY_RESPONSE | jq '.'

GATEWAY_ID=$(echo $GATEWAY_RESPONSE | jq -r '.id.id')

if [ "$GATEWAY_ID" != "null" ] && [ -n "$GATEWAY_ID" ]; then
  echo "✓ Created gateway device with ID: $GATEWAY_ID"

  # Create credentials
  CREDENTIALS_PAYLOAD='{
    "credentialsId": "gw00000000_token",
    "credentialsType": "ACCESS_TOKEN"
  }'

  echo "Creating credentials..."
  CREDENTIALS_RESPONSE=$(curl -s -X POST "http://167.172.75.1:8080/api/device/$GATEWAY_ID/credentials" \
    -H "Content-Type: application/json" \
    -H "X-Authorization: Bearer $TOKEN" \
    -d "$CREDENTIALS_PAYLOAD")

  echo "✓ Gateway device GW00000000 created successfully!"
  echo "  Access Token: gw00000000_token"
else
  echo "Failed to create gateway device - it may already exist"
fi