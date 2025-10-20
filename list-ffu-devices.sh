#!/bin/bash

# Load configuration
if [ -f .env.ebmpapst-gateway ]; then
    export $(cat .env.ebmpapst-gateway | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
fi

REST_URL=${REST_URL:-http://167.99.64.71:8080}
REST_USERNAME=${REST_USERNAME:-tenant@thingsboard.org}
REST_PASSWORD=${REST_PASSWORD:-tenant}

# Login
TOKEN=$(curl -s -X POST "$REST_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" \
    | jq -r '.token')

echo "Devices with type EBMPAPST_FFU:"
curl -s -X GET "$REST_URL/api/tenant/devices?deviceType=EBMPAPST_FFU&pageSize=20&page=0" \
    -H "X-Authorization: Bearer $TOKEN" | jq -r '.data[] | .name'

echo ""
echo "Total DW devices (type=default):"
curl -s -X GET "$REST_URL/api/tenant/devices?pageSize=1000&page=0" \
    -H "X-Authorization: Bearer $TOKEN" | jq -r '.data[] | select(.name | startswith("DW"))' | jq -s 'length'
