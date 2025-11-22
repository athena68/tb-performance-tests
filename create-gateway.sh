#!/bin/bash

echo "=== Creating Gateway Device GW00000000 ==="

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

# Get EBMPAPST_FFU device profile ID
PROFILE_RESPONSE=$(curl -s -X GET "http://167.172.75.1:8080/api/tenant/deviceProfiles?pageSize=100&page=0" \
  -H "X-Authorization: Bearer $TOKEN")

PROFILE_ID=$(echo $PROFILE_RESPONSE | jq -r '.data[] | select(.name=="EBMPAPST_FFU") | .id.id')

if [ -z "$PROFILE_ID" ] || [ "$PROFILE_ID" = "null" ]; then
  echo "EBMPAPST_FFU device profile not found, creating it..."

  # Create device profile
  PROFILE_PAYLOAD='{
    "name": "EBMPAPST_FFU",
    "type": "default",
    "image": null,
    "description": "EBMPAPST FFU Device Profile",
    "profileData": {
      "configuration": {
        "type": "DEFAULT"
      },
      "transportConfiguration": {
        "type": "DEFAULT"
      },
      "provisionConfiguration": {
        "type": "DISABLED"
      },
      "alarms": [
        {
          "id": "HIGH_TEMPERATURE_ALARM",
          "alarmType": "HIGH_TEMPERATURE_ALARM",
          "createRules": {
            "enabled": true
          },
          "propagate": true,
          "description": "High temperature alarm",
          "severity": "CRITICAL"
        }
      ]
    }
  }'

  PROFILE_RESPONSE=$(curl -s -X POST "http://167.172.75.1:8080/api/tenant/deviceProfiles" \
    -H "Content-Type: application/json" \
    -H "X-Authorization: Bearer $TOKEN" \
    -d "$PROFILE_PAYLOAD")

  PROFILE_ID=$(echo $PROFILE_RESPONSE | jq -r '.id.id')

  if [ -z "$PROFILE_ID" ] || [ "$PROFILE_ID" = "null" ]; then
    echo "Failed to create device profile"
    echo $PROFILE_RESPONSE | jq '.'
    exit 1
  fi

  echo "Created device profile with ID: $PROFILE_ID"
else
  echo "Found existing EBMPAPST_FFU profile: $PROFILE_ID"
fi

# Create gateway device
GATEWAY_PAYLOAD='{
  "name": "GW00000000",
  "type": "EBMPAPST_FFU",
  "label": "EBMPAPST FFU Gateway 00000000",
  "additionalInfo": {
    "gateway": true,
    "description": "EBMPAPST FFU Gateway Device"
  }
}'

echo "Creating gateway device..."
GATEWAY_RESPONSE=$(curl -s -X POST "http://167.172.75.1:8080/api/tenant/device" \
  -H "Content-Type: application/json" \
  -H "X-Authorization: Bearer $TOKEN" \
  -d "$GATEWAY_PAYLOAD")

GATEWAY_ID=$(echo $GATEWAY_RESPONSE | jq -r '.id.id')

if [ -z "$GATEWAY_ID" ] || [ "$GATEWAY_ID" = "null" ]; then
  echo "Failed to create gateway device"
  echo $GATEWAY_RESPONSE | jq '.'
  exit 1
fi

echo "✓ Created gateway device GW00000000 with ID: $GATEWAY_ID"

# Create gateway credentials (Access Token)
CREDENTIALS_PAYLOAD='{
  "credentialsId": "gw00000000_token",
  "credentialsType": "ACCESS_TOKEN",
  "credentialsValue": "gw00000000_token"
}'

echo "Creating gateway credentials..."
CREDENTIALS_RESPONSE=$(curl -s -X POST "http://167.172.75.1:8080/api/device/$GATEWAY_ID/credentials" \
  -H "Content-Type: application/json" \
  -H "X-Authorization: Bearer $TOKEN" \
  -d "$CREDENTIALS_PAYLOAD")

echo "✓ Created gateway credentials"
echo ""
echo "Gateway Summary:"
echo "  Name: GW00000000"
echo "  ID: $GATEWAY_ID"
echo "  Access Token: gw00000000_token"
echo "  Device Profile: EBMPAPST_FFU ($PROFILE_ID)"
echo ""
echo "The gateway device is now ready for MQTT connections!"