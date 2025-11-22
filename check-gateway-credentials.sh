#!/bin/bash

echo "=== Checking Gateway Device Credentials ==="

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

# Find the gateway device GW00000000
echo "Searching for gateway device GW00000000..."
DEVICES_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/devices?pageSize=100&page=0" \
  -H "X-Authorization: Bearer $TOKEN")

GATEWAY_ID=$(echo $DEVICES_RESPONSE | jq -r '.data[] | select(.name=="GW00000000") | .id.id')

if [ -z "$GATEWAY_ID" ] || [ "$GATEWAY_ID" = "null" ]; then
  echo "Gateway GW00000000 not found!"
  exit 1
fi

echo "Found gateway GW00000000 with ID: $GATEWAY_ID"

# Get gateway device credentials
echo "Getting gateway credentials..."
CREDENTIALS_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/device/$GATEWAY_ID/credentials" \
  -H "X-Authorization: Bearer $TOKEN")

echo "Gateway credentials:"
echo $CREDENTIALS_RESPONSE | jq '.'

# Check if credentials exist and are properly formatted
CREDENTIALS_ID=$(echo $CREDENTIALS_RESPONSE | jq -r '.id.id')
CREDENTIALS_TYPE=$(echo $CREDENTIALS_RESPONSE | jq -r '.credentialsType')
CREDENTIALS_VALUE=$(echo $CREDENTIALS_RESPONSE | jq -r '.credentialsId')

echo ""
echo "Credentials Summary:"
echo "  ID: $CREDENTIALS_ID"
echo "  Type: $CREDENTIALS_TYPE"
echo "  Value: $CREDENTIALS_VALUE"

if [ "$CREDENTIALS_TYPE" = "null" ] || [ -z "$CREDENTIALS_TYPE" ]; then
  echo "⚠️  WARNING: Gateway has no credentials type set!"
fi

if [ "$CREDENTIALS_VALUE" = "null" ] || [ -z "$CREDENTIALS_VALUE" ]; then
  echo "⚠️  WARNING: Gateway has no credentials value set!"
fi